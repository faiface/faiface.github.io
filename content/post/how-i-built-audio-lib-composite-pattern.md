---
title: "How I built an audio library using the composite pattern and higher-order functions"
date: 2017-08-13T16:21:12+02:00
draft: false
---

Some people say that Go can't express good abstractions. They mostly refer to the lack of generics.
That's because in most object-oriented languages, people are used to creating abstractions around
types. In Go, the right way is to create abstractions around behaviour using interfaces. When you
follow this principle, you find that Go is very powerful at creating abstractions.

In this post, I am going to explore a way of creating abstractions using the *'good old composite
pattern'* from the book called 'Design patterns'. Combined with higher-order functions, this pattern
is not only powerful, but also convenient. I will

1. Explain what the composite pattern is.
2. Show how it can be combined with *higher-order functions* and closures.
3. Present a way I used it to create an **audio library**.

**Why the hell are you going to talk about design patterns? Those are for Java and Java is bad, we
don't like design patterns in Go!**

Uhm, well, you're right, we usually don't like design patterns in Go. But, bear with me, this is
only going to be about one of them and it's gonna be interesting, I promise.

## First example: arithmetic expressions

The composite pattern revolves around a single idea:

***Everything satisfies a single interface and complex things are composed from simple ones.***

It might not be entirely clear what this means, so let's dive directly into the code.

In this first example, we'll be creating a system to create and evaluate arithmetic expressions. We
need to start by creating the *one single interface*. It's clear that an interface representing an
*expression* will be the right choice. This way, we'll be able to create simple expressions and
create more complicated expressions by composing simpler ones using various operators.

To make things even simpler, we won't even define an interface. A function type is sufficient here.

```go
type Expr func() float64
```

So, an expression is a function which evaluates to `float64`. An interface equivalent would be an
interface with a single method, say `Eval`.

The most simple expression is one that returns a constant. Let's call it `Const`. Here's the
constructor.

```go
func Const(x float64) Expr {
        return func() float64 {
                return x
        }
}
```

Now we can define a composite constructor, say a one which sums other expressions. It takes an
aribirary number of other expressions and evaluates to their sum.

```go
func Sum(exs ...Expr) Expr {
        return func() float64 {
                sum := 0.0
                for _, ex := range exs {
                        sum += ex()
                }
                return sum
        }
}
```

The expression returned from the `Sum` constructor simply adds the results of the other expressions
together. Note, that we call `ex()` inside the loop, because the `Expr` type is a function and
calling it yields the result.

Now we have some material to start using our arithmetic expressions library.

```go
ex1 := Sum(Const(1), Const(2), Const(3))
fmt.Println(ex1()) // prints 6

ex2 := Sum(Const(1), Sum(Const(2), Const(3)))
fmt.Println(ex2()) // prints 6 alike
```

We can create more expressions. `Ref` always returns the value of a variable it is pointing to.

```go
func Ref(x *float64) Expr {
        return func() float64 {
                return *x
        }
}
```

And now we can do funny things :)

```go
x := 1.0
ex := Sum(Ref(&x), Ref(&x))

x = ex() // x = 2
x = ex() // x = 4
x = ex() // x = 8
x = ex() // x = 16
```

I think this is neat. This is just a little toy example, to give you the taste. Let's go ahead to
another example. Still a toy one, but a little less toy one.

## Second example: sequences

Now, we will use the composite pattern to assemble sequences of numbers. Finite or inifinite,
doesn't matter.

Once again, we need to start by creating the single interface. Obviously, this interface will
represent a sequence. The interface will contain a single method called `Next`. This method returns
the next element in the sequence and `true` or `false` depending on whether we already reached the
end of the sequence.

```go
type Seq interface {
        Next() (x float64, ok bool)
}
```

We could use a function type again, but I decided to use a proper interface, for clarity.
Nonetheless, we can create a helper function type, which will simplify creating instances of the
interface.

```go
type SeqFunc func() (x float64, ok bool)

func (sf SeqFunc) Next() (x float64, ok bool) {
        return sf()
}
```

The `SeqFunc` is a function type which satisfies the `Seq` interface by implementing the `Next`
function returning the result of itself. This pattern is also used in the standard library with
[`http.HandlerFunc`](https://golang.org/pkg/net/http/#HandlerFunc).

Let's start creating actual `Seq` implementations.

The simplest one is a sequence created from a slice. We'll call it `Mk` (make a sequence).

```go
func Mk(vals ...float64) Seq {
        i := 0
        return SeqFunc(func() (x float64, ok bool) {
                if i >= len(vals) {
                        return 0, false
                }
                x = vals[i]
                i++
                return x, true
        })
}
```

`Mk` sequence tracks the current index in the slice it was created from. Every time `Next` is
called, the current value is returned and the index is incremented. When we reach the end of the
slice, we simply return `0, false`.

A complement function to `Mk` is `Collect`, which takes a `Seq` and collects it into a slice of
numbers. This is obviously only applicable to finite sequences.

```go
func Collect(s Seq) []float64 {
        var vals []float64
        for {
                x, ok := s.Next()
                if !ok {
                        break
                }
                vals = append(vals, x)
        }
        return vals
}
```

Now, we can turn a slice into a sequence and back again, very useful.

```go
fmt.Println(Collect(Mk(1, 2, 3))) // prints [1 2 3]
```

We can create an infinite sequence of natural numbers.

```go
func Naturals() Seq {
        n := 0.0
        return SeqFunc(func() (x float64, ok bool) {
                n++
                return n, true
        })
}
```

And we can create a composite which takes `n` first elements out of any sequence.

```go
func Take(n int, s Seq) Seq {
        return SeqFunc(func() (x float64, ok bool) {
                if n <= 0 {
                        return 0, false
                }
                n--
                return s.Next()
        })
}
```

Now, we can generate `n` first natural numbers.

```go
fmt.Println(Collect(Take(10, Naturals())))
// [1 2 3 4 5 6 7 8 9 10]
```

This is starting to feel like functional programming. And rightfully so. We are doing

1. Composition
2. Lazy evaluation and infinite sequences
3. Too long expressions :)

The first point is the most important. With the composite pattern, we've been able to create
building blocks and compose more complicated things out of them. Don't believe me? Let's create a
`Split` function, which takes a sequence and splits it into two sequences at a given index. *Just
watch!*

```go
func Split(n int, s Seq) (l, r Seq) {
        return Mk(Collect(Take(n, s))...), s
}
```

That was easy! Make sure to understand it, should be fairly obvious.

To make the `Split` function, we didn't have to write almost any code. All of the required pieces
were already present, we just needed to compose them in the right way. Hence, the composite pattern.

Let's see how our `Split` function behaves.

```go
s := Take(7, Naturals())
l, r := Split(4, s)
fmt.Println(Collect(l), Collect(r))
// [1 2 3 4] [5 6 7]
```

Take seven naturals, split them at four and print the results. Simple, right?

When using the composite pattern, you'll find it very easy to follow the DRY principle and you
usually end up writing much less code than otherwise.

**Excercise:** Create a `Dup` (duplicate) function, which takes a `Seq` and returns two `Seq`s which
are both identical (in terms of elements) to the original `Seq`. It should work for infinite
sequences too.

## Real thing: Beep audio library

Now that you've certainly got a hang of the composite pattern, let's see how it can be used in a
real library. The library I'm talking about is an audio library I've been working on for the past
month. It's called [Beep](https://github.com/faiface/beep), which is a name chosen from a [poll on
Reddit](https://www.reddit.com/r/golang/comments/6n1plq/choose_the_name_for_a_new_audio_library_in_go/).

First things first, the library is by no means only my work. The playback heavily depends on Hajime
Hoshi's [Oto](https://godoc.org/github.com/hajimehoshi/oto) library and MP3 decoding depends on his
[go-mp3](https://github.com/hajimehoshi/go-mp3) package.

The library is built around the composite pattern, for a great good. Let's take a look!

### The `Streamer` interface

As usual, when designing around the composite pattern, the first thing is the single interface. In
case of Beep, this single interface is called `Streamer`. It's very similar to the former one,
`Seq`.

Audio is composed of elements called
[*samples*](https://en.wikipedia.org/wiki/Sampling_(signal_processing)). A sample is a number on the
timeline in the interval [-1, +1] which specifies the pressure of the air at that moment. A
`Streamer` is pretty much a sequence of samples. However, getting the samples one by one as with
`Seq` would be way too inefficient. That's why the `Streamer` interface is designed to stream a
number of samples at once.

Here's how it looks like.

```go
type Streamer interface {
        Stream(samples [][2]float64) (n int, ok bool)
        Err() error
}
```

The `Stream` method is given a slice of samples (there are two numbers per sample, the left and the
right channel), fills it with samples and advances the internal state (if any). It returns the
number of samples it streamed (filled in the slice). If the `Streamer` already reached it's end and
has no samples to stream, it returns `false`. Otherwise, it returns `true`. The complete description
can be found in the [docs](https://godoc.org/github.com/faiface/beep#Streamer).

The `Err` method is for handling errors, such as file and network errors. Errors are kept out of the
`Stream` method to simplify composition.

Similar to `Seq`, there is a helper function type which enables easy creation of `Streamer`s that
can't error.

```go
type StreamerFunc func(samples [][2]float64) (n int, ok bool)
```

### Loading audio files

Enough talking, let's get to the code.

The simplest way to create a streamer is from an audio file. Beep currently supports
[WAV](https://godoc.org/github.com/faiface/beep/wav) and
[MP3](https://godoc.org/github.com/faiface/beep/mp3) formats. We'll be ignoring errors here, for
simplicity, don't do that in real code.

```go
// import "github.com/faiface/beep/mp3"
file, _ := os.Open("song.mp3")
streamer, format, _ := mp3.Decode(file)
```

This creates a streamer which streams the song directly from the file without loading it in the
memory first. The song doesn't even have to fit in the memory, since it's never fully there.

The `format` return value tells us some information about the source file, such as the [sample
rate](https://en.wikipedia.org/wiki/Sampling_(signal_processing)#Sampling_rate) (number of samples
per second) and the number of channels.

Let's go a head and convert the MP3 file into a WAV file. We've already created a streamer for the
MP3 file, so all we need to do is to encode this streamer into a WAV file.

```go
// import "github.com/faiface/beep/wav"
output, _ := os.Create("song.wav")
wav.Encode(output, streamer, format)
output.Close()
```

This is quite spectacular. *There is no MP3 to WAV conversion functionality in the library
anywhere.* What is there is an MP3 to `Streamer` functionality and `Streamer` to WAV functionality.
Composing these two things yields an MP3 to WAV converter. Furthermore, this converter **operates
directly on the files, doesn't load the files into the memory**. You can convert gigabytes of audio
data without ruining your RAM. **All of this simply follows from the chosen composite interface and
its composition.**

## Playing through the `speaker`

Loading and saving audio files is interesting, but playing is the key. Beep has an extension package
`"github.com/faiface/beep/speaker"`, which allows playback of arbitrary streamers.

First, we need to initialize the speaker, which involves setting the speaker's sample rate and
buffer size. This is done using the `Init` function.

```go
// import (
//         "github.com/faiface/beep"
//         "github.com/faiface/beep/speaker"
// )
sr := beep.SampleRate(48000)
speaker.Init(sr, sr.N(time.Second/10))
```

The type [`beep.SampleRate`](https://godoc.org/github.com/faiface/beep#SampleRate) is an `int` with
two methods. First, `sr.D`, converts number of samples to their duration in `time.Duration`. The
second, `sr.N`, does the opposite. Since `speaker.Init` takes the number of samples in the buffer,
we use the `sr.N` method to calculate the number of samples in 1/10s. Smaller buffer size means more
responsive playback (lower latency). Larger buffer size means more reliable playback.

To play a streamer, we simply call the `speaker.Play` function.

```go
speaker.Play(streamer)
```

This starts the playback and returns immediately.

Following this, here's how to play an MP3 file.

```go
file, _ := os.Open("song.mp3")
streamer, format, _ := mp3.Decode(file)

sr := format.SampleRate
speaker.Init(sr, sr.N(time.Second/10))
speaker.Play(streamer)
```

Nice! There is a problem with this code, though. This program immediately exits and we won't hear
anything. The solution would be to either wait infinitely using `select {}`, or somehow wait until
the song ends. We'll learn about that in the following section.

## Composing `Streamer`s

Beep provides a number of built-in streamer compositors. Let's take a look at a few of them.

One of the most important ones is `Seq`. Don't get confused, this has nothing to do with the
sequence composite interface above. It takes some streamers and streams them one after another.
Here's how it's implemented.

```go
func Seq(s ...Streamer) Streamer {
        i := 0
        return StreamerFunc(func(samples [][2]float64) (n int, ok bool) {
                for i < len(s) && len(samples) > 0 {
                        sn, sok := s[i].Stream(samples)
                        samples = samples[sn:]
                        n, ok = n+sn, ok || sok
                        if !sok {
                                i++
                        }
                }
                return n, ok
        })
}
```

Pretty simple. I'm not going to explain it in detail, you can do that yourself if you want. What's
more important is how we can use this compositor.

```go
speaker.Play(beep.Seq(streamer1, streamer2))
```

This code plays two different streamers one after another. *Note, that a streamer is not immutable
and gets drained after playing. Therefore `beep.Seq(streamer1, streamer1)` will not play the same
streamer twice, because on the second time it will already be drained.*

Another useful streamer is `Callback`. This is a streamer which streams no audio, but instead calls
a function when it starts streaming (and ends streaming immediately).

With this knowledge, we are ready to play a song until it ends.

```go
done := make(chan struct{})
speaker.Play(beep.Seq(
        streamer,
        beep.Callback(func() {
                close(done)
        })
))
<-done
```

We create a channel which will signal the end of the song. Then, we play a sequence of the song and
a callback. Therefore, when the song finishes, the callback gets called. The callback closes the
signaling channel and causes the receive operation proceed. Neat.

**What if we want to play a streamer which streams at a different sample rate than the speaker?** If
you'd just play it as it is, the playback would be either too fast or too slow. Beep provides a
`Resample` compositor exactly for this.

Let's say we have a streamer which streams at the sample rate of `44100`, but we initialized the
speaker to the sample rate of `48000`. Here's how we do it.

```go
speaker.Play(beep.Resample(4, 44100, 48000, streamer))
```

The first argument is the resampling quality. Read more about it in the
[docs](https://godoc.org/github.com/faiface/beep#Resample).

Resampling can also be used to speed up or slow down an audio.

```go
twiceAsFast := beep.ResampleRatio(4, 2, streamer)
speaker.Play(twiceAsFast)
```

Beep provides a variety of other compositor. Let's list a few.

```go
playTogether := beep.Mix(streamer1, streamer2)

firstFiveSeconds := beep.Take(sr.N(5*time.Second), streamer3)

ctrl := beep.Ctrl{Streamer: streamer4}
ctrl.Paused = true

minuteOfSilence := beep.Silence(sr.N(time.Minute))

louder := effects.Gain{
        Streamer: streamer5,
        Gain:     2,
}

toTheLeft := effects.Pan{
        Streamer: streamer6,
        Pan:      -1,
}
```

Of course, if the built-in compositors and streamers are not enugh, **you can easily create your own
ones.** All you need to do is to implement a `Streamer`. For example, here's an infinite sine wave
streamer. Of course, you can use `beep.Take` on it to turn it into a finite streamer.

```go
func SineWave(sr beep.SampleRate, freq float64) beep.Streamer {
        t := 0.0
        return beep.StreamerFunc(func(samples [][2]float64) (n int, ok bool) {
                for i := range samples {
                        y := math.Sin(math.Pi * freq * t)
                        samples[i][0] = y
                        samples[i][1] = y
                        t += sr.D(1).Seconds()
                }
                return len(samples), true
        })
}
```

## Conclusion

This article showed what the composite pattern is, how it can be combined with higher-order
functions and closures for convenience and how you can use it to create **flexible and reusable
code.**

Of course, the composite pattern is not a fit for everything. But when it is, **please consider
using it**, as it will greatly improve the quality and DRYness of your code.

I think it's a great fit for Go and an idiomatic solution to many abstraction problems. **Go has
interfaces and higher-order functions, so use them!**

Currently, I'm figuring out how to incorporate the composite pattern into my
[Pixel](https://github.com/faiface/pixel) game library. If you have any ideas on that, please share
;)

Michal Štrba