# oxlang: the ox programming language 🐂

ox is a intepreted, dynamic programming language inspired by [Cub] (no relation to the [2011] one.)
Its syntax borrows heavily from Cub itself and [golang].

Since ox keeps most of Cub's semantics, existing Cub code should run in ox without any changes (backward-compatible).

ox is not meant to be a production language: rather as an experiment in implementing a programming language entirely in Python.

## Why the name ox?

Because the zodiac animal this year is Ox, and to go along with the animal-themed names.

## Todo

- [x] finish basic parser
- [ ] code working intepreter 
- [ ] add module system
- [ ] add ability to interface Python modules

## Examples

```swift
// ox is kind of like untyped Swift (which is also what Cub was aiming for).
// Currently, these primitive types are supported:

// Strings (to have double quotes in a string, use single quotes, and vice versa.)
// Of course, UTF-8 is supported.
my_var = "Hello World!"

// Numbers are all floating-point as in Cub.
// Like Python, variables do not have a fixed type, and can be reassigned.
// (The '.0' can be omitted.)
my_var = 42

// Booleans can either be true or false.
// Comparisons will return a boolean.
a_bool = true
is_the_answer_to_life_and_everything = my_var >= 42

// Arrays are analogous to lists.
// To append, use '+='.
an_array = [4, 2, 0]
an_array += 1

// Functions define an operation so you don't have to keep copying and pasting the same section of code.
func pi() {
  return 3.141592
}

// Structs are similar to Go/C structs.
// Members are defined inside its scope.
struct Point {
  x, y
}
p = Point(0, 0)

// The biggest feature borrowed from Go is probably struct methods.
// A struct method (shown below) accepts a instance of the struct, plus any other parameter.
// The first arg should be named self, but you can name it something else.
func Point.distance(self) {
  return (self.x ^ 2) + (self.y ^ 2)
}

// Structs can inherit members and methods from other structs.
// New members can be defined on top of the inherited struct's definition.
struct RelativePoint inherits Point {
  cx, cy
}

func Point.relative_distance(self) {
  return (abs(self.cx - self.x) ^ 2) + (abs(self.cy - self.y) ^ 2)
}
```

[2011]: https://en.wikipedia.org/wiki/Ox_(programming_language)
[Cub]: https://github.com/louisdh/cub
[golang]: https://golang.org
