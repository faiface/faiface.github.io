---
title: "Context should go away for Go 2"
date: 2017-08-06T18:58:25+02:00
draft: false
---

As usual, when a new blog post comes out on [blog.golang.org](https://blog.golang.org/), I'm all
eager to read it as soon as possible. The most recent one, [Contributors
Summit](https://blog.golang.org/contributors-summit), is a nice write-up on the issues that the Go
contributors have been talking about. While reading it, I stumbled upon a sentence that made me
write this post. Here is is:

> For instance, it would be nice if io.Reader accepted a context so that blocking read operations
> could be canceled. 

This gave me chills. This is what `io.Reader` would look like with a context.

```go
type Reader interface {
        Read(ctx context.Context, p []byte) (n int, err error)
}
```

I did some research and found that some people already [proposed this
change](https://github.com/golang/go/issues/20280) for Go 2. Thankfully it received a decent amount
of thumbs down, so it's likely not making it.

This post is about all of the things that are wrong with the `"context"` package, why it is useful
 despite that, and that Go 2 should do something about it. So, grab some popcorn and let's get
 started!

## Go is a general purpose language

First things first, let's establish some ground. Go is a *good* language for writing servers, but Go
is not a *language for writing servers*. Go is a *general purpose programming language*, just like
C, C++, Java or Python. For example, I've been using Go for about 2 years and I've never written a
single server in it.

For this reason, when designing the Go language and it's standard library, we need to approach it
from a general purpose language perspective. Now, I'm not trying to say that context is only useful
for server people. But mostly, it is.

## Context is like a virus

This is the first and most important problem with context: it spreads! As mentioned in [this blog
post about the context package](https://blog.golang.org/context):

> At Google, we require that Go programmers pass a Context parameter as the first argument to every
> function on the call path between incoming and outgoing requests.

Every such function also needs to propagate the context down it's call path, or else it wouldn't be
fully cancelable. This means that all the potentially slow functions from other libraries that are
being called from a function accepting a context should also accept a context.

In short, if you're writing a library that has function which can take some significant amount of
time and your library is *potentially* going to be used by a server application, you have to accept
a context in those functions.

That's how context spreads like a virus. What's bad about that? Let's recap:

1. Go is a general purpose language.
2. If a library is *potentially* going to be used by a server, it should accept a context.
3. Now, everyone has to deal with the context, even the ones who don't need it.

Of course, I can just pass `context.TODO()` everywhere, but that's just gross, it hurts readability,
makes my code look ugly and simply removes a part of fun I have with Go.

If the Go language ever comes to the point where I'd have to write this

```go
n, err := r.Read(context.TODO(), p)
```

put a bullet in my head, please.

You might argue: *A library can provide two version of each function, one with a context and one
without a context.* Sure, just take a look at the
[`"database/sql"`](https://golang.org/pkg/database/sql/) package. Although it does solve the problem
partially, it smells quite bad.

Also, imagine teaching Go to a student. You start explaining the context-equipped `io.Reader`
interface (or anything else which occasionally requires a context) to them and they ask: *What is
that `ctx context.Context` thingy there?* And the answer would probably just be: *Don't worry about
that, just pass `context.TODO()` there for now.* Sounds a lot like `public static void` to me.

The message is: Context spreads like a virus and I (alongside almost everyone who doesn't write
servers in Go) don't want to deal with it when I don't have to.

## The `"context"` package itself is not that good

The first thing is a personal opinion, but for me, the `context.Context` interface has too many
methods. Now, the more serious problems.

### If you use `ctx.Value` in my (non-existent) company, you're fired

I'm not sure who came up with this idea that context should carry a map of meaningless objects to
meaningless objects. There are just so many things that are wrong with it. Let's list a few:

1. An obvious one, it's not statically typed at all.
2. It requires documenting which values (keys and their types) a certain function supports and uses.
   As we all know, documentation is mostly a code that never runs.
3. It's very similar to thread-local storage. We know how bad of an idea thread-local storage is.
   Non-flexible, complicates usage, composition, testing.
4. This probably doesn't happen often, but it's prone to name collisions.
5. It's just magic. An error-prone magic.

I know that `ctx.Value` makes some things easier. But, I believe that designing your APIs without
`ctx.Value` in mind at all makes it always possible to come up with alternatives.

### Context is mostly an inefficient linked list

The way `WithCancel`, `WithDeadline`, etc. constructors from the `"context"` package work is they
create a linked list. Among other things, this sometimes requires creating a
[goroutine](https://golang.org/src/context/context.go#L261) for `WithCancel`, which propagates
cancelation signals from the previous context to the new one. Of course, if the context is never
canceled, this goroutine is leaked.

The `WithValue` constructor takes a context and returns a context which propagates the previous
context but also contains a value under the specified key. This is, obviously, achieved by creating
another node in the linked list, the purpose of which is to return the correct value for that key
and propagate the previous context otherwise. So, `ctx.Value` is not only a map of meaningless
objects to meaningless objects, it's also a terribly slow map of meaningless objects to meaningless
objects.

### And lastly

```go
ctx context.Context
```

is a lot like

```
Foo foo = new Foo();
```

One of the things Go was [created to avoid](https://www.youtube.com/watch?v=rKnDgT73v8s).

## What does the `"context"` package actually solve?

Despite all of the bad things described above, the `"context"` package is genuinely useful, because
it solves one thing that is kinda hard to do in Go: **cancelation**. That's the only problem the
`"context"` package really solves (or attempts to solve).

Let's face it, cancelation in Go is hard. There is a whole talk called ['Advanced Go Concurrency
Patterns'](https://www.youtube.com/watch?v=QDDwwePbDtw), which discusses this problem in depth. This
talk happened before the `"context"` package was introduced into the Go standard library and thus it
discusses solutions to the cancelation problem which only involve simple channels.

There are number of reasons why solutions proposed in the talk don't scale very well. Here are a few
of them:

1. The cancelation channels are usually not accepted by other libraries and functions and thus
   cancelation is only possible 'in-between' the slow operations.
2. Considering a ‘tree of goroutines’ (where children goroutines are the ones spawned by the parent
   goroutines), it's easy to cancel the whole tree (just close the cancelation channel), but it's
   harder to cancel a sub-tree (you need to introduce another channel for that, or some other
   solution).

The `"context"` package does solve these problems. Inefficiently and with numerous problems, but
solves them better than anything else out there. **In Go, we need to be able to solve the
cancelation problem**. Solving it is usually necessary anytime a decent usage of goroutines is
involved.

## Go 2 should explicitly address the cancelation problem

I think it's a weakness of the Go programming language that we needed to introduce a package like
`"context"`. Go makes it very easy to create goroutines and communicate between them. However, the
`"context"` package is a proof that Go makes it hard enough to *arrange goroutines to finish*. I
believe this problem should be solved directly in the language. The language should provide a
solution, which is:

1. Simple and elegant.
2. Optional, non-intrusive and non-infectious.
3. Robust and efficient.
4. Only solves the cancelation problem. Values can be omitted. Timeouts can also be implemented on
   top of a very simple cancelation.

You might argue: *I like context, it's an elegant solution to the problem without changing or
complicating the language*. I disagree. For all the reasons described above it's not an elegant
solution and although it's not an integral part of the language, it is and is becoming more and more
an integral part of the libraries. In the end, it makes the language harder to use.

I have a few solutions in mind, but I'll leave them for another post or a proposal, or I'll leave
them for myself if someone comes up with a better solution. The purpose of this post is just to
point out the problem.

## Conclusion

This post was trying to point out a problem in the Go language. In short, cancelation is a problem
in Go and the `"context"` package does not solve this problem very well. I can't think of any other
solution that would solve this problem good except for a language change. That is up for Go 2.

Thanks for reading and I'm looking forward to your feedback and ~~hate comments~~ objections ;).

Michal Štrba
