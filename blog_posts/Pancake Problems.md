---
tags:
  - Mathematics
publish date: June 9th, 2024
subtitle: Stacks on stacks on stacks on stacks
---
Recently I read through *The Simpsons and Their Mathematical Secrets* by Simon Singh. On top of being a fun reminder of a lot of episodes from the golden age of the show, it is a fantastic survey of many subjects and anecdotes in math. It's a great read even if you don't think you have all of the background knowledge as Simon is very good about giving a quick overview of prerequisite knowledge for the various topics he touches on. One topic in particular infected me. That is, the titular Pancake Problem.

The [Pancake Problem](https://en.wikipedia.org/wiki/Pancake_sorting) goes like this: You're given a stack of pancakes all of different sizes, but they're in a random order. You want to modify the stack so that they are ordered from largest on the bottom to smallest on the top, making a visually pleasing pyramid. However, the only way you can modify the stack is to stick your spatula in-between two pancakes and flip everything above your spatula in one go. With this setup in mind, the problem asks "What is the minimum number of flips required for an arbitrary stack of size *N*". That minimum count is known as the "Pancake number" of *N*

This is one of those problems which I find absolutely beautiful. Similar to something like the [time consuming and relationship destroying Collatz conjecture](https://xkcd.com/710/) or the [Moving Sofa Problem](https://en.wikipedia.org/wiki/Moving_sofa_problem) it's one of those things that's explainable in a few sentences but with a solution which is surprisingly rich in depth. There are permutations of the problem (see the Wikipedia page linked above) but I find the base problem very elegant. However, a closed form for the Pancake number of *N* is still yet to be found. We have brute forced quite a few (22 at the time of writing) values, but you can imagine that checking every sequence of flips on every permutation of N pancakes is very costly. Upper and lower bounds have been found and slowly squeezed over time with the hope that eventually they will meet in the middle and give us our closed form.

After reading about this problem, I found myself thinking about it a lot over the coming days. I decided to not look into any of the progress the mathematics community has made and try my hand at it. I figured it wasn't likely that I would find a solution, but maybe I could get some unexplored ideas.

# Formalization

I wanted to formalize the problem to get some rigor to it. I eventually came to a formal definition of the stack of pancakes:

$$S_n=(s_i: s_i \in [1,n])\ s.t.\ \forall j\in[1,n]\  \exists s_i=j\  \land |S_n| = n$$
Or in English, $S_n$ is a sequence of natural numbers from $1$ to $n$ where each in that range are present once and only once. I then called the set of all valid $S_n$-s "$\mathbb{S}_n$".

I then rigorously defined this "flip" operation and came to the following:

$$F_k(S_n) = \{f_{k,n}(s_i): \forall i \in S_n\} $$
where

$$
f_{k,n}(s_i) = \begin{cases}
s_i& i<k\\
s_{n-i+k}& i\geq k
\end{cases}
$$

This then results in a sequence of flips (like the one which yields the pancake number of $N$) being defined as a chain of compositions of various $F_k$-s. I decided to define a sequence of $m$ flips as:

$$
\textbf{F}(S_n)=(F_{j_1}\circ F_{j_2} \circ \ldots \circ F_{j_{m-1}} \circ F_{j_m})(S_n)
$$

What is not immediately intuitive is that, since composition is commonly defined as right associative, you would read this sequence of flips from right to left. I also, for convenience of this problem, use $|\textbf{F}|$ to denote the number of functions composed in this sequence.

Further, I said that the set of all possible $\textbf{F}$-s for a given $n$ to be $\mathbb{F}_n$. Lastly, I defined some special objects in these sets:

1. The "Target Stack" is simply the sorted sequence of pancakes
$$
\bar{S}_n=\{1, 2, \ldots, n-1, n\}
$$

2. The "Solution Stack" $S^*_n$ is the initial condition stack which corresponds to the pancake number of n
3. And the "Solution Sequence" $\textbf{F}^*_n$ is the sequence of moves which gets the solution stack to the target stack

$$ \bar{S}_n=\textbf{F}^\*_n(S^\*_n) $$

Finally we can get to the formal definition of the pancake number $P(n)$. All it is is:

$$
P(n)=\max_{S_n\in\mathbb{S_n}}\min_{\textbf{F}\in\mathbb{F}_n}|\textbf{F}(S_n)|\  s.t.\ \textbf{F}(S_n) = \bar{S}_n
$$

Again in English: "Take every permutation of pancakes of length $n$, take every possible sequence of flips which result in the target stack when applied to the permutation and the length of the smallest sequence of flips is the pancake number"

# Playing Around

## Finding the Inverse of a Flip
Immediately, I wanted to show the intuition that applying the same flip twice resulted in the same stack you started with. With the above definition, this is equivalent to proving that $F_k$ is its own inverse. That is:

$$(F_k \circ F_k) (S_n) = S_n$$

This is actually fairly trivial to prove just from the definition of $F_k$. Note that:

$$(F_k \circ F_k)(S_n) = \{f_{k,n}(f_{k,n}(s_i)):\  \forall s_i \in S_n\}$$

$$f_{k,n}(f_{k,n}(s_i))=\begin{cases}
s_i& i<k \\
s_{n-(n-i+k)+k} & i\geq k
\end{cases} $$

i.e.

$$f_{k,n}(f_{k,n}(s_i))=\begin{cases}
s_i& i<k \\
s_{i} & i\geq k
\end{cases} = s_i $$ 
What's neat about this conclusion is that it illuminates a bit about what the solution sequence looks like. The solution sequence cannot have any two subsequent flips of the same $k$, because they would simply collapse to the identity function.
## Finding more properties

There was one invariant that I noticed that I figured could be helpful. From the definition of $f_{k,n}$ , every element in a stack below $k$ is untouched. Given the definition of a sequence of flips (copied from above):

$$ \textbf{F}(S_n)=(F_{j_1}\circ F_{j_2} \circ \ldots \circ F_{j_{m-1}} \circ F_{j_m})(S_n)$$
It follows that
$$ \textbf{F}(S_n) = [s_1, s_2, \ldots , s_{k-1}]\ |\ R $$
where $k=\min_{j_{i}\ i < m}i$  , $|$ represents concatenation of sequences and $R$ is some sequence of the elements of the elements of $S_n$ not in the first sequence of the concatenation. In clearer words, all elements below the lowest flip in a given sequence are untouched.

This actually immediately results in the conclusion that the solution stack cannot start with a subsequence of ordered terms. The proof of this is simple, as you can take any stack of this type and trivially make a "worse" stack (and thus one which would result in a higher pancake number) by flipping over the whole thing.

That conclusion then leads to the conclusion that, since a stack which starts with just the 1st element in the right place fits the above definition, the first element cannot be in place for the solution stack. And since you cannot modify the bottom element without flipping the whole stack (see the invariant described above), the solution sequence *must* involve $F_1$

Great, so we now know $P(n) > 1\ :\ n\neq1$ . Good work.

I was then thinking about an upper bound. Immediately, a strategy to solve any sequence comes to mind. 
<pre><code>for each element i from 1 to n:
	find s_k=i
	perform F_k
	perform F_i
</code></pre>

Note that at each iteration, this strategy moves the "target pancake" to the top of the stack and then sends it to the bottom of the unsorted stack. This algorithm does 2 flips for each pancake so we now now $P(n)\leq2n$


That's some pretty good progress! Let's finally take a look at what the rest of the mathematicians have figured out. Just a quick glance at that Wikipedia page and....

> The minimum number of flips required to sort any stack of _n_ pancakes has been shown to lie between $\frac{15}{14n}$ and $\frac{18}{11n}$

oh.

> In 2011, ... [it was] prove[n] that the problem of finding the shortest sequence of flips for a given stack of pancakes is NP-Hard

oh.
## Other Discoveries

Small road block. I don't understand how I haven't managed to get as good of answers as 50 years of much more qualified people working on this problem. I mean I spent a whole weekend thinking about this! Oh well. Some other neat discoveries I made before checking out some other resources are:

### Graph Representation

You can represent the problem in a bit of a different way by considering a bi-graph where each node is a permutation of pancakes of length $n$. and there exists edges between two nodes where a flip can convert one sequence into the other. This re-frames the problem as finding the furthest node from the node corresponding to the target stack and finding the length of the shortest path from that node to the node of the target stack. Certainly you could use some graph theory machinery to make some progress-

[Oh](https://en.wikipedia.org/wiki/Pancake_sorting#Pancake_graphs)

### Cycling entries

I found a neat property that you can do a right [circular shift](https://en.wikipedia.org/wiki/Circular_shift) of a subsequence $[s_i, s_{i+1}, \ldots,s_{j-1},s_j]$ by applying the sequence $f_k \circ f_{k=1} \circ \ldots \circ f_{i+1} \circ f_i$   . Similarly, the reverse sequence rotates that subsequence left. 

### Uniqueness of the Solution Sequence

While playing around, I ran into a handful of postulates which I could only prove to the point of depending on the uniqueness of a solution sequence $\textbf{F}^*_n$. That is, that there is only one sequence which corresponds the pancake number $P(n)$. Try as I might, I was unable to definitively prove this. Maybe someone else out there has an idea or maybe I just haven't reframed the problem right 

# Closing Thoughts

Despite the lack of real solid progress on this problem, it was fun to think about. When I stumble across problems like this I really do like to try to tackle them myself before seeing what other people have done to make progress on it. I seldom think I'm going to do anything groundbreaking, but that is actually a nice weight off my shoulders. It means I can just focus on having fun with the puzzle.

Also as a fun aside, one of the papers (William H. Gates, Christos H. Papadimitriou, "*Bounds for sorting by prefix reversal*")  which progressed this problem has a unique co-author. He's more widely known as "Bill" Gates. This is (as far as I know) the only mathematical publication he has ever been cited on.