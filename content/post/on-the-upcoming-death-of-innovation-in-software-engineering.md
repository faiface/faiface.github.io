---
title: "On the Upcoming Death of Innovation in Software Engineering"
date: 2026-10-17T18:15:25+02:00
draft: true
---

As coding agents grow more capable and reliable, software engineers are building faster, while spending less time with the code itself. But building more is not the same as making progress. For decades, programming innovation --- by which I mean creating new abstractions --- has been driven by the **symbiosis** of building and invention. It was a virtuous cycle of deep study, intimacy with the code, friction and dissatisfaction, lightbulb moments, recognition and adoption by the industry, and back to the deep study of the new abstractions. I fear that this cycle is being dismantled by the current paradigm shift, because it was always built on _side-effects_ of how we used to work: we were paid to build, not to invent. We might end up in a sort of "dark ages" of software engineering, stuck with today's languages and frameworks for much longer than warranted.

## What Is an Abstraction?

In _The Lord of the Rings_, at the entrance to Khazad-dûm, the Fellowship was presented with a puzzle. The inscription on the door said _"Speak, friend, and enter"_, and the door would not open unless somebody spoke the correct spell. The spell --- "mellon", the word for "friend" in Elvish --- put in motion the heavy stones guarding the mines that once brought wealth and fame to the Dwarves.

We programmers are magicians of the real world. We don't just cast spells, we create them!

```javascript
const response = await fetch(url);
```

A handful of words, and an unimaginable number of electrons are set in motion to fulfill the cast spell. But unlike the spells from fairy tales, and unlike the words of natural language (more on that later), the spells we create are **real.** On the surface, they look just like wishes to the _Genie of the Lamp_, but underneath, there is no Genie. Instead, there is code, and beneath that code, there is more code, and if we dig deep enough, we end up touching physical reality.

The spells we create are constructed in full, not wished into existence, and therefore, they contain all the reality that makes them happen, including the constraints and the trade-offs. That's also what makes them hard to create! I could say _"put all of Wikipedia on my disk, but don't take more than 1ms"_, but it won't work. I could say anything, but words don't work; code does.

We call these spells **abstractions,** and all of today's software rests on them.

A good abstraction takes fewer words to **precisely** describe _what_ it does than _how_ it does it. An abstraction needs both, and the _how_ is what makes it real, but the user of the abstraction only needs to care about the _what_, which makes it useful. For example, the _what_ of a `sort` function is that it reorders an array such that each element is greater than or equal to the previous one. On the other hand, the _how_ can be hundreds or thousands of lines of code, and the programmer doesn't need to care!

### Isn't Natural Language the Ultimate Abstraction?

"The hottest new programming language is English," said Andrej Karpathy on Twitter in 2023. And many people agree that a language like English is the natural culmination of what we've been doing by inventing new programming languages. Long gone are the days when we looked at machine code, and perhaps soon, we won't look at any code at all!

A programming language compiles to machine code, and English "compiles" to code by an agent! It sounds like the same thing, but no, it is _very_ different. Coding agents are "just" programmers. When a company outsources its software to a third party, they don't claim to be programming via Zoom meetings; they understand they are not programming, they are outsourcing. A coding agent is much the same: I am not programming by prompting it, the agent is programming. You can see it in the fact that the agent still needs to _write code,_ and utilize the languages and libraries that we have created to make building complex software possible.

**But isn't that just a more sophisticated kind of compilation?** An agent, running on a computer, turns prompts into code. A compiler turns high-level code into machine code. What's the difference?

The difference is that you can't make a compiler better at compiling by giving it a good library. The idea doesn't even make sense: a compiler doesn't _use_ abstractions, it _is_ an abstraction. It has the _what_, and it has the _how_. It's a real thing, and it just works!

But a coding agent does benefit from better tools and abstractions, because it is a programmer, not a compiler. Just like a human, a coding agent only has so much mental capacity (the context window), so being able to express more in fewer lines of code does help. Catching errors sooner with a good type system or better debugging tools helps too, since agents make mistakes. In fact, it seems like whatever we were inventing over the past decades to make _our_ programming life easier is just as beneficial for agents as for us!

There's also a deeper reason why natural language is not the next step in abstraction:

**Natural language is not an abstraction.**

There, I said it. Natural language is vague and imprecise, but vagueness is _not_ abstraction. As noted by Edsger W. Dijkstra in his 1972 Turing Award lecture _The Humble Programmer_:

> The purpose of abstracting is not to be vague, but to create a new semantic level in which one can be absolutely precise.

True abstractions deliver on their promises at any scale, and they compose in predictable ways. Their _what_ is precise, and their _how_ is robust. Natural language does not, and cannot, do that. Whether we are programming manually, or using coding agents, the true abstractions at our disposal will always ultimately determine how far we can go.

### Do We Really Need More Abstractions?

It's quite obvious that the current abstractions have not caught up with the software that we develop. We enjoy robust type checking within the boundaries of a single program, but the distributed structure of our cloud applications is stitched together with YAML files. There is no solid, agreed-upon way of solving persistence, so we spend time developing data layers, integrating with databases, trying to avoid deadlocks and race conditions. There used to be a new web UI framework every other week, because UI is genuinely hard, and we have not fully figured it out yet.

There is so much more to solve!

However, I have to concede one thing. We can already do _a lot_ with what we have today, and that may be part of the problem, because most innovation has not been driven by an outright _impossibility_ of building software. Rather, it was motivated by deficiencies in the way it was done, and by love for the craft. Only later, as those innovations stacked up, did they open entirely new horizons, unlocking possibilities not imagined or attempted before.

## How Innovation Happens

TODO