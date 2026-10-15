---
title: "How to use 'try'"
date: 2019-07-04T19:28:03+02:00
draft: false
---

The recent [`try` proposal](https://github.com/golang/go/issues/32437) by Robert Griesemer sparked a lot of controversy. While the proposal is a subject to reasonable criticism, I didn't feel like everyone was always on the same page.

This post isn't pro-try or anti-try. It just shows how `try` could be used so that you can form a more informed opinion.

Suppose we are grad students of social sciences and need to come up with idea for a poll. Since we are programmers, too, we've come up with this poll: find correlations between person's gender, favorite OS, and favorite programming language.

This is, of course, a contrived example. The goal of this post isn't to solve a real-world scenario, but to show multiple aspects of `try` in a small program.

The data from the poll will look like this:

```go
name: Boris Bateman
gender: man
os: Windows
lang: PHP

name: Darin May
gender: woman
os: OSX
lang: JavaScript

name: Shea Wilks
gender: nonbinary
os: Linux
lang: Emacs LISP

name: Robert Griesemer
gender: man
os: Linux
lang: Go
```

Each respondent has four required fields: **name**, **gender**, **os**, and **lang**. There is an obligatory empty line between respondents.

We want to parse this file into a slice of `Respondent` structs, defined like this:

```go
type Respondent struct {
	Name   string
	Gender string
	OS     string
	Lang   string
}
```

Let's get on to it, step by step!

```go
func parseRespondents(path string) (resps []Respondent, err error) {
	return nil, nil
}
```

I know, I could have used an `io.Reader`. But, for the purposes of demonstrating `try`, let's keep it this way.

First, we're gonna use a (not yet existing) function `fmt.HandleErrorf`:

```go
func parseRespondents(path string) (resps []Respondent, err error) {
	defer fmt.HandleErrorf(&err, "parse %s", path)
	return nil, nil
}
```

It adds context to the returned error, if it's not `nil`. It's defined like this:

```go
func HandleErrorf(err *error, format string, args ...interface{}) {
	if *err != nil {
		*err = errors.Wrapf(*err, format, args...)
	}
}
```

Every error returned from `parseRespondents("respondents.txt")` will now be prefixed with `parse respondents.txt:`.

```go
func parseRespondents(path string) (resps []Respondent, err error) {
	defer fmt.HandleErrorf(&err, "parse %s", path)

	f := try(os.Open(path))
	defer f.Close()

	return nil, nil
}
```

Normally, `os.Open(path)` returns two values: the file and an error. By wrapping it in `try`, we drop the error from the return values and get an automatic return if the error wasn't `nil`.

What kind of error do we get now if the file doesn't exist?

```go
parse respondnts.txt: open respondnts.txt: no such file or directory
```

The error has all the context it needs, because `os.Open` adds some context on its own.

```go
func parseRespondents(path string) (resps []Respondent, err error) {
	defer fmt.HandleErrorf(&err, "parse %s", path)

	file := try(os.Open(path))
	defer file.Close()

	scanner := bufio.NewScanner(file)

	for {
		//TODO: parse fields
	}

	return resps, nil
}
```

Now it's time to create a helper function for parsing the individual fields.

```go
func parseField(scanner *bufio.Scanner, name string) (value string, err error) {
	defer fmt.HandleErrorf(&err, "parse field %s", name)

	if !s.Scan() {
		return "", io.EOF
	}

	prefix := name + ":"
	if !strings.HasPrefix(s.Text(), prefix) {
		return "", fmt.Errorf("expected %q", prefix)
	}

	return strings.TrimPrefix(s.Text(), prefix), nil
}
```

Once again, we use `fmt.HandleErrorf` to add a context to all errors returned from this function. This time, we tell which field we were trying to parse.

We try scanning the line. If successful, we try and trim the required prefix (e.g. `"name:"`, `"gender:"`, ...) from the beginning of the line and return the resulting value of the field.

Let's now use this helper function in `parseRespondents`.

First, we need to try and parse the first field of a respondent: the name. If we reached the end of file, that's fine, we need to stop parsing. Otherwise, we need to report the error. This is not a situation for `try`, because we need to deal with the error in a more complex way than just returning it.

```go
for {
	name, err := parseField(scanner, "name")
	if errors.Is(err, io.EOF) { // can't use ==, because the error is wrapped
		break
	}
	if err != nil {
		return resps, err
	}

	//TODO: parse the remaining fields
}
```

Once we parsed the name, we need to parse all the remaining fields. These are required to be there, so we can use `try` in this situation:

```go
for {
	name, err := parseField(scanner, "name")
	if errors.Is(err, io.EOF) { // can't use ==, because the error is wrapped
		break
	}
	if err != nil {
		return resps, err
	}

	resp := Respondent{
		Name:   name,
		Gender: try(parseField(scanner, "gender")),
		OS:     try(parseField(scanner, "os")),
		Lang:   try(parseField(scanner, "lang")),
	}

	resps = append(resps, resp)
}
```

Without `try`, we would have to manually check the error for each of the fields, resulting in many lines of code. Here, we can simply use the value returned from the `try` directly, `try` will take care of returning the possible error.

All that's remaining is the obligatory empty line:

```go
for {
	name, err := parseField(scanner, "name")
	if errors.Is(err, io.EOF) { // can't use ==, because the error is wrapped
		break
	}
	if err != nil {
		return resps, err
	}

	resp := Respondent{
		Name:   name,
		Gender: try(parseField(scanner, "gender")),
		OS:     try(parseField(scanner, "os")),
		Lang:   try(parseField(scanner, "lang")),
	}

	resps = append(resps, resp)

	if !s.Scan() {
		break
	}
	if s.Text() != "" {
		return resps, errors.New("expected empty line")
	}
}
```

And here's the whole function:

```go
func parseRespondents(path string) (resps []Respondent, err error) {
	defer fmt.HandleErrorf(&err, "parse %s", path)

	f := try(os.Open(path))
	defer f.Close()

	s := bufio.NewScanner(f)

	for {
		name, err := parseField(s, "name")
		if errors.Is(err, io.EOF) {
			break
		}
		if err != nil {
			return resps, err
		}

		resp := Respondent{
			Name:   name,
			Gender: try(parseField(s, "gender")),
			OS:     try(parseField(s, "os")),
			Lang:   try(parseField(s, "lang")),
		}

		resps = append(resps, resp)

		if !s.Scan() {
			break
		}
		if s.Text() != "" {
			return resps, errors.New("expected empty line")
		}
	}

	return resps, nil
}
```

What do the error messages look like? Here are some of them:

```go
parse respondents.txt: parse field gender: expected "gender:"
parse respondents.txt: expected empty line
parse respondents.txt: parse field lang: EOF
```

Not that bad. One thing that's definitely missing is **line numbers**. Could we add them?

Let's add a line counter variable:

```go
defer fmt.HandleErrorf(&err, "parse %s", path)

f := try(os.Open(path))
defer f.Close()

s := bufio.NewScanner(f)

line := 1
```

We need to increment it each time we read a line, so let's change the `parseField` function to do that:

```go
func parseField(s *bufio.Scanner, line *int, name string) (value string, err error) {
	defer fmt.HandleErrorf(&err, "scan field '%s'", name)

	if !s.Scan() {
		return "", io.EOF
	}

	prefix := name + ":"
	if !strings.HasPrefix(s.Text(), prefix) {
		return "", fmt.Errorf("expected %q", prefix)
	}

	*line++
	return strings.TrimPrefix(s.Text(), prefix), nil
}
```

And modify all its usages:

```go
name, err := parseField(s, &line, "name")
if errors.Is(err, io.EOF) {
	break
}
if err != nil {
	return resps, err
}

resp := Respondent{
	Name:   name,
	Gender: try(parseField(s, &line, "gender")),
	OS:     try(parseField(s, &line, "os")),
	Lang:   try(parseField(s, &line, "lang")),
}
```

We also need to increment the counter when scanning the empty line:

```go
if !s.Scan() {
	break
}
if s.Text() != "" {
	return resps, errors.New("expected empty line")
}
line++
```

And now, let's use `fmt.HandleErrorf` to add the line to the error. How do we do that?

This **won't** work:

```go
line := 1
defer fmt.HandleErrorf(&err, "line %d", line)
```

This would always add `line 1` because the arguments to a deferred function are evaluated immediately.

This also wouldn't work:

```go
line := 1
defer fmt.HandleErrorf(&err, "line %d", &line)
```

Instead of adding a line number, this would will the address of the `line` variable. Not what we wanted.

This **would** be a solution:

```go
defer func() {
	if err != nil {
		err = errors.Wrapf(err, "line %d", line)
	}
}()
```

And it's a perfectly fine solution.

However, there is a *neater* (although a little hackier) solution. What if we made a type called `Ref` that would hold a pointer and would dereference it when required to print itself? Then we could do this:

```go
defer fmt.HandleErrorf(&err, "line %v", Ref{&line})
```

We can make such a type quite easily. Here's what it looks like when we only care about pointers to `int`:

```go
type Ref struct {
	Pointer *int
}

func (r Ref) String() string {
	return fmt.Sprint(*r.Pointer)
}
```

And here's a general solution for all types:

```go
type Ref struct {
	Pointer interface{}
}

func (r Ref) String() string {
	val := reflect.ValueOf(r.Pointer).Elem().Interface()
	return fmt.Sprint(val)
}
```

Not that hard.

The errors are now more helpful:

```go
parse respondents.txt: line 12: parse field gender: expected "gender:"
parse respondents.txt: line 9: expected empty line
parse respondents.txt: line 4: parse field lang: EOF
```

Finally, here's the whole program:

```go
package main

import (
	"bufio"
	"fmt"
	"io"
	"os"
	"reflect"
	"strings"

	"github.com/pkg/errors"
)

type Ref struct {
	Pointer interface{}
}

func (r Ref) String() string {
	val := reflect.ValueOf(r.Pointer).Elem().Interface()
	return fmt.Sprint(val)
}

type Respondent struct {
	Name   string
	Gender string
	OS     string
	Lang   string
}

func parseField(s *bufio.Scanner, line *int, name string) (value string, err error) {
	defer fmt.HandleErrorf(&err, "scan field '%s'", name)

	if !s.Scan() {
		return "", io.EOF
	}

	prefix := name + ":"
	if !strings.HasPrefix(s.Text(), prefix) {
		return "", fmt.Errorf("expected %q", prefix)
	}

	*line++
	return strings.TrimPrefix(s.Text(), prefix), nil
}

func parseRespondents(path string) (resps []Respondent, err error) {
	defer fmt.HandleErrorf(&err, "parse %s", path)

	f := try(os.Open(path))
	defer f.Close()

	s := bufio.NewScanner(f)

	line := 1
	defer fmt.HandleErrorf(&err, "line %v", Ref{&line})

	for {
		name, err := parseField(s, &line, "name")
		if errors.Is(err, io.EOF) {
			break
		}
		if err != nil {
			return resps, err
		}

		resp := Respondent{
			Name:   name,
			Gender: try(parseField(s, &line, "gender")),
			OS:     try(parseField(s, &line, "os")),
			Lang:   try(parseField(s, &line, "lang")),
		}

		resps = append(resps, resp)

		if !s.Scan() {
			break
		}
		if s.Text() != "" {
			return resps, errors.New("expected empty line")
		}
		line++
	}

	return resps, nil
}

func main() {
	resps, err := parseRespondents("respondents.txt")
	if err != nil {
		fmt.Println(err)
		return
	}
	fmt.Println(resps)
}
```

In summary, here are the main points of this post:

1. Don't decorate what's already decorated (e.g. `os.Open`).
2. Use `fmt.HandleErrorf` to add context.
3. For more granularity, break it into more functions (e.g. `parseField`).
4. There's no shame in falling back to `if err != nil` if appropriate.

I hope I illustrated multiple aspects of the proposed `try` function and associated error handling constructs like `fmt.HandleErrorf` and showed cases where it's usable and also cases where it's not. Form your own opinion on it and feel free to speak about it in the comments here or on [Reddit](https://www.reddit.com/r/golang/comments/c9eo3g/how_to_use_try_faiface_blog/) :). Thanks for reading!
