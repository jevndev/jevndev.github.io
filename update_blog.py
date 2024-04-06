from __future__ import annotations

import dataclasses
import typing
import datetime
import pathlib
import itertools
import yaml
import io
import rich.progress
import markdown
import shutil
from dateutil import parser

BLOG_POST_DATA_FOLDER = pathlib.Path("./blog_posts")
BLOG_POST_PAGE_FOLDER = pathlib.Path("./blog")

POST_HEADER_DELIMITER = "---\n"

TAG_KEY = "tags"
PUBLISH_DATE_KEY = "publish date"
EXPECTED_KEYS = (TAG_KEY, PUBLISH_DATE_KEY)


PostTitle = typing.NewType("PostTitle", str)
PostBody = typing.NewType("PostBody", str)
PostTag = typing.NewType("PostTag", str)


def _string_iterable_to_stream(strings: typing.Iterable[str]) -> io.StringIO:
    return io.StringIO("".join(strings))


def _parse_as_yaml(lines: typing.Iterable[str]) -> typing.Mapping[str, typing.Any]:
    return yaml.safe_load(_string_iterable_to_stream(lines))


def _has_expected_keys(header_data: typing.Mapping[str, typing.Any]) -> bool:
    return all(key in header_data for key in EXPECTED_KEYS)


@dataclasses.dataclass(frozen=True)
class PostMetadata:
    tags: typing.Sequence[PostTag]
    publish_date: datetime.datetime

    @staticmethod
    def from_post_header_text(header_lines: typing.Iterable[str]) -> PostMetadata:
        header_data = _parse_as_yaml(header_lines)
        assert _has_expected_keys(header_data)
        return PostMetadata(
            [PostTag(tag) for tag in header_data[TAG_KEY]],
            parser.parse(header_data[PUBLISH_DATE_KEY]),
        )


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
    def _make_html(blog_post: BlogPost) -> HTMLstr:
        return HTMLstr(markdown.markdown("".join(blog_post.body)))

    @staticmethod
    def _get_path(blog_post: BlogPost) -> pathlib.Path:
        return (
            pathlib.Path(str(blog_post.metadata.publish_date.year))
            / str(blog_post.metadata.publish_date.month)
            / str(blog_post.metadata.publish_date.day)
            / blog_post.post_title.replace(" ", "_")
        ).with_suffix(".html")

    @staticmethod
    def from_blog_post(
        blog_post: BlogPost, blog_post_root_folder: pathlib.Path
    ) -> BlogPostPage:
        return BlogPostPage(
            blog_post,
            BlogPostPage._make_html(blog_post),
            blog_post_root_folder / BlogPostPage._get_path(blog_post),
        )

    def _ensure_path_exists(self):
        for path in reversed(self.page_path.parents):
            path.mkdir(exist_ok=True)

    def write_file(self):
        self._ensure_path_exists()
        with open(self.page_path, "w") as f:
            f.write(self.html)


def generate_blog_post_pages(
    blog_posts: typing.Sequence[BlogPost], blog_post_root_folder: pathlib.Path
) -> typing.Sequence[BlogPostPage]:
    pages: typing.List[BlogPostPage] = []

    reset_blog_pages(blog_post_root_folder)

    for blog_post in blog_posts:
        page = BlogPostPage.from_blog_post(blog_post, blog_post_root_folder)
        page.write_file()
        pages.append(page)

    return pages


def reset_blog_pages(blog_post_root_folder: pathlib.Path):
    assert blog_post_root_folder.exists() and blog_post_root_folder.is_dir()
    shutil.rmtree(blog_post_root_folder)
    blog_post_root_folder.mkdir()


def update_blog_homepage(pages: typing.Sequence[BlogPostPage]): ...


def update_rss(pages: typing.Sequence[BlogPostPage]): ...


def main():
    blog_posts = get_blog_posts(BLOG_POST_DATA_FOLDER)
    blog_post_pages = generate_blog_post_pages(blog_posts, BLOG_POST_PAGE_FOLDER)

    update_blog_homepage(blog_post_pages)
    update_rss(blog_post_pages)


if __name__ == "__main__":
    main()
