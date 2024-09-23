from __future__ import annotations

import dataclasses
import datetime
import io
import uuid
import itertools
import pathlib
import shutil
import typing
import xml.etree.ElementTree

import markdown
import rich.progress
import yaml
from bs4 import BeautifulSoup, Tag
from dateutil import parser

HTMLID = typing.NewType("HTMLID", str)

BLOG_POST_DATA_FOLDER = pathlib.Path("./blog_posts")
BLOG_POST_PAGE_FOLDER = pathlib.Path("./blog")
BLOG_LIST_PAGE = pathlib.Path("./blog.html")
BLOG_POST_TEMPLATE_PAGE = pathlib.Path("blog_post_template.html")

POST_LIST_ID = HTMLID("post_list")

POST_HEADER_DELIMITER = "---\n"

TAG_KEY = "tags"
PUBLISH_DATE_KEY = "publish date"
REQUIRED_KEYS = (TAG_KEY, PUBLISH_DATE_KEY)

POST_TITLE_ID = HTMLID("post_title")
POST_SUBTITLE_ID = HTMLID("post_subtitle")

POST_CONTENT_ID = HTMLID("post_content")

SUBTITLE_KEY = "subtitle"

BLOG_TITLE = "Jonathan Evans Blog"
HOMEPAGE = "https://www.jonathanevans.dev/"
BLOG_LINK = HOMEPAGE + str(BLOG_LIST_PAGE)
BLOG_DESCRIPTION = "A blog about programming, math and other fascinations"

PostTitle = typing.NewType("PostTitle", str)
PostSubtitle = typing.NewType("PostSubtitle", str)
PostBody = typing.NewType("PostBody", str)
PostTag = typing.NewType("PostTag", str)


def _string_iterable_to_stream(strings: typing.Iterable[str]) -> io.StringIO:
    return io.StringIO("".join(strings))


def _parse_as_yaml(lines: typing.Iterable[str]) -> typing.Mapping[str, str]:
    return yaml.safe_load(_string_iterable_to_stream(lines))


def _has_required_keys(header_data: typing.Mapping[str, str]) -> bool:
    return all(key in header_data for key in REQUIRED_KEYS)


@dataclasses.dataclass(frozen=True)
class PostMetadata:
    tags: typing.Sequence[PostTag]
    publish_date: datetime.datetime
    subtitle: typing.Optional[PostSubtitle]

    @staticmethod
    def from_post_header_text(header_lines: typing.Iterable[str]) -> PostMetadata:
        header_data = _parse_as_yaml(header_lines)
        assert _has_required_keys(header_data)

        tags = [PostTag(tag) for tag in header_data[TAG_KEY]]
        publish_date = parser.parse(header_data[PUBLISH_DATE_KEY])
        if SUBTITLE_KEY in header_data:
            subtitle = PostSubtitle(header_data[SUBTITLE_KEY])
        else:
            subtitle = None

        return PostMetadata(tags, publish_date, subtitle)

    def subtitle_or(self, /, default="") -> str:
        return self.subtitle if self.subtitle is not None else default


def _is_header_delimiter(text: str) -> bool:
    return text == POST_HEADER_DELIMITER


def _is_not_header_delimiter(text: str) -> bool:
    return not _is_header_delimiter(text)


@dataclasses.dataclass(frozen=True)
class BlogPost:
    metadata: PostMetadata
    post_title: PostTitle
    body: PostBody

    @dataclasses.dataclass(frozen=True)
    class _PartitionedFile:
        header_text: typing.Iterable[str]
        body_text: typing.Iterable[str]

    @staticmethod
    def _extract_header_and_body_text(
        file_lines: typing.Iterable[str],
    ) -> _PartitionedFile:
        first_line, *remaining_lines = file_lines
        assert _is_header_delimiter(first_line)

        header_lines = itertools.takewhile(_is_not_header_delimiter, remaining_lines)
        unused_delimiter_line, *body_lines = itertools.dropwhile(
            _is_not_header_delimiter, remaining_lines
        )

        return BlogPost._PartitionedFile(header_lines, body_lines)

    @staticmethod
    def _get_post_title(file: pathlib.Path) -> PostTitle:
        return PostTitle(file.stem)

    @staticmethod
    def from_file(file: pathlib.Path) -> BlogPost:
        post_title = BlogPost._get_post_title(file)
        with open(file, "r") as file_lines:
            file_parts = BlogPost._extract_header_and_body_text(file_lines)
            post_metadata = PostMetadata.from_post_header_text(file_parts.header_text)
            return BlogPost(
                post_metadata,
                post_title,
                PostBody("".join(file_parts.body_text)),
            )


def get_blog_posts(
    blog_post_folder: pathlib.Path,
) -> typing.Sequence[BlogPost]:
    assert blog_post_folder.is_dir()

    blog_posts: typing.List[BlogPost] = []

    for post in rich.progress.track(
        list(blog_post_folder.glob("*.md")),
        description="Parsing Posts",
        show_speed=True,
    ):
        blog_posts.append(BlogPost.from_file(post))

    return blog_posts


HTMLstr = typing.NewType("HTMLstr", str)


@dataclasses.dataclass(frozen=True)
class BlogPostPage:
    source_data: BlogPost
    html: HTMLstr
    page_path: pathlib.Path

    @staticmethod
    def _set_text_by_id(html: BeautifulSoup, content: str, id_: HTMLID):
        element = html.find(attrs={"id": id_})
        assert isinstance(element, Tag)
        element.string = content

    @staticmethod
    def _set_post_title(html: BeautifulSoup, title: PostTitle, id_: HTMLID):
        BlogPostPage._set_text_by_id(html, title, id_)

    @staticmethod
    def _set_post_subtitle(html: BeautifulSoup, title: PostSubtitle, id_: HTMLID):
        BlogPostPage._set_text_by_id(html, title, id_)

    @staticmethod
    def _set_post_content(html: BeautifulSoup, content: HTMLstr, post_body_id_: HTMLID):
        post_body_element = html.find(attrs={"id": post_body_id_})

        assert isinstance(post_body_element, Tag)
        post_body_element.append(BeautifulSoup(content, "html.parser"))

    @staticmethod
    def _make_html(blog_post: BlogPost, template_html: BeautifulSoup) -> HTMLstr:
        BlogPostPage._set_post_title(template_html, blog_post.post_title, POST_TITLE_ID)

        if blog_post.metadata.subtitle is not None:
            BlogPostPage._set_post_subtitle(
                template_html, blog_post.metadata.subtitle, POST_SUBTITLE_ID
            )

        blog_post_content = HTMLstr(markdown.markdown("".join(blog_post.body)))

        BlogPostPage._set_post_content(
            template_html, blog_post_content, POST_CONTENT_ID
        )

        blog_post_page = HTMLstr(str(template_html.prettify()))

        return blog_post_page

    @staticmethod
    def _get_path(blog_post: BlogPost) -> pathlib.Path:
        return (
            pathlib.Path(str(blog_post.metadata.publish_date.year))
            / str(blog_post.metadata.publish_date.month)
            / str(blog_post.metadata.publish_date.day)
            / blog_post.post_title.replace(" ", "_")
        )

    @staticmethod
    def from_blog_post(
        blog_post: BlogPost,
        blog_post_root_folder: pathlib.Path,
        template_page_path: pathlib.Path,
    ) -> BlogPostPage:
        with open(template_page_path, "r") as f:
            template_page = BeautifulSoup(f, "html.parser")

        return BlogPostPage(
            blog_post,
            BlogPostPage._make_html(blog_post, template_page),
            blog_post_root_folder / BlogPostPage._get_path(blog_post),
        )

    def _ensure_path_exists(self):
        for path in reversed(self.page_path.parents):
            path.mkdir(exist_ok=True)

    def write_file(self):
        self._ensure_path_exists()
        with open(self.page_path, "w") as f:
            f.write(self.html)

    def make_bs4_card_tag(
        self,
    ) -> Tag:
        post_entry = BeautifulSoup(
            f"""
<li class="post">
    <div class="post_title_bar">
        <h3 class="post_title">
            <a href="{self.page_path}">
                {self.source_data.post_title}
            </a>
        </h3>
        <div class="date">
            {self.source_data.metadata.publish_date.strftime("%Y/%m/%d")}
        </div>
    </div>
    {'' if self.source_data.metadata.subtitle is None else f'<p class="blurb">{self.source_data.metadata.subtitle}</p>'}
</li>""",
            "html.parser",
        )

        post_tags_div = post_entry.new_tag("div", attrs={"class": "tags"})

        for tag in self.source_data.metadata.tags:
            post_tags_div.append(
                BeautifulSoup(f"""<div class="tag">{tag}</div>""", "html.parser")
            )

        assert post_entry.li is not None

        post_entry.li.insert(-1, post_tags_div)
        return post_entry

    @property
    def uuid(self):
        return uuid.uuid5(uuid.NAMESPACE_URL, str(self.page_path))


def get_blog_post_url_relative_to(post: BlogPostPage, root: str) -> str:
    return root + str(post.page_path)


def generate_blog_post_pages(
    blog_posts: typing.Sequence[BlogPost], blog_post_root_folder: pathlib.Path
) -> typing.Sequence[BlogPostPage]:
    pages: typing.List[BlogPostPage] = []

    reset_blog_pages(blog_post_root_folder)

    for blog_post in rich.progress.track(
        blog_posts, "Generating posts", show_speed=True
    ):
        page = BlogPostPage.from_blog_post(
            blog_post,
            blog_post_root_folder,
            BLOG_POST_TEMPLATE_PAGE,
        )
        page.write_file()
        pages.append(page)

    return pages


def reset_blog_pages(blog_post_root_folder: pathlib.Path):
    assert blog_post_root_folder.exists() and blog_post_root_folder.is_dir()
    shutil.rmtree(blog_post_root_folder)
    blog_post_root_folder.mkdir()


def add_post_break(post_list_element: Tag):
    post_list_element.append(
        BeautifulSoup("""<hr class="post_break" />""", "html.parser")
    )


def update_blog_homepage(
    pages: typing.Sequence[BlogPostPage], blog_list_homepage_path: pathlib.Path
):
    with open(blog_list_homepage_path, "r") as f:
        blog_list_page_html = BeautifulSoup(f, "html.parser")
        overwrite_list_page_html(pages, blog_list_page_html)

    with open(blog_list_homepage_path, "w") as f:
        f.write(blog_list_page_html.prettify())


def overwrite_list_page_html(
    pages: typing.Sequence[BlogPostPage], blog_list_page_html: BeautifulSoup
):
    post_list_element = blog_list_page_html.find(attrs={"id": POST_LIST_ID})
    assert isinstance(post_list_element, Tag)

    post_list_element.clear()
    add_post_break(post_list_element)
    for page in rich.progress.track(
        pages, description="Updating Homepage", show_speed=True
    ):
        post_list_element.append(page.make_bs4_card_tag())
        add_post_break(post_list_element)


class RSSFeed:
    def __init__(self, title: str, link: str, description: str):
        self._channel = self._make_channel(title, link, description)
        self._feed = self._make_feed(self._channel)

    def _make_feed(
        self, channel: xml.etree.ElementTree.Element
    ) -> xml.etree.ElementTree.Element:
        feed = xml.etree.ElementTree.Element("rss")
        feed.set("version", "2.0")
        feed.set("xmlns:atom", "http://www.w3.org/2005/Atom")
        feed.append(channel)

        return feed

    def _make_channel(
        self, title: str, link: str, description: str
    ) -> xml.etree.ElementTree.Element:
        channel = xml.etree.ElementTree.Element("channel")

        title_element = xml.etree.ElementTree.Element("title")
        title_element.text = title
        channel.append(title_element)

        link_element = xml.etree.ElementTree.Element("link")
        link_element.text = link
        channel.append(link_element)

        description_element = xml.etree.ElementTree.Element("description")
        description_element.text = description
        channel.append(description_element)

        atom_link = xml.etree.ElementTree.Element("atom:link")
        atom_link.set("href", BLOG_LINK)
        atom_link.set("rel", "self")
        atom_link.set("type", "application/rss+xml")
        channel.append(atom_link)

        return channel

    def add_item(
        self,
        title: str,
        link: str,
        description: str,
        pub_date: datetime.datetime,
        uuid: uuid.UUID,
    ):
        item = xml.etree.ElementTree.Element("item")

        title_element = xml.etree.ElementTree.Element("title")
        title_element.text = title
        item.append(title_element)

        link_element = xml.etree.ElementTree.Element("link")
        link_element.text = link
        item.append(link_element)

        description_element = xml.etree.ElementTree.Element("description")
        description_element.text = description
        item.append(description_element)

        guid_element = xml.etree.ElementTree.Element("guid")
        guid_element.set("isPermaLink", "false")
        guid_element.text = str(uuid)
        item.append(guid_element)

        pub_date_element = xml.etree.ElementTree.Element("pubDate")

        # Wed, 02 Oct 2002 08:00:00 EST
        pub_date_element.text = pub_date.strftime("%a, %d %b %Y %H:%M:%S CST")
        item.append(pub_date_element)

        self._channel.append(item)

    def add_blog_post(self, blog_post: BlogPostPage):
        self.add_item(
            blog_post.source_data.post_title,
            get_blog_post_url_relative_to(blog_post, HOMEPAGE),
            blog_post.source_data.metadata.subtitle_or(""),
            blog_post.source_data.metadata.publish_date,
            blog_post.uuid,
        )


def update_rss(pages: typing.Sequence[BlogPostPage]):
    feed = RSSFeed(BLOG_TITLE, BLOG_LINK, BLOG_DESCRIPTION)
    for page in pages:
        feed.add_blog_post(
            page,
        )

    with open(BLOG_POST_PAGE_FOLDER / "rss.xml", "w") as f:
        print(xml.etree.ElementTree.tostring(feed._feed).decode(), file=f)


def main():
    blog_posts = get_blog_posts(BLOG_POST_DATA_FOLDER)
    blog_post_pages = generate_blog_post_pages(blog_posts, BLOG_POST_PAGE_FOLDER)

    update_blog_homepage(blog_post_pages, BLOG_LIST_PAGE)
    update_rss(blog_post_pages)


if __name__ == "__main__":
    main()
