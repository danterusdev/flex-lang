# Flex
A language created with flexibility in mind. Inspired by a random idea I had in my head that I thought would be both cool and pretty funny.

## More Info
At its core, Flex is a essentially a stack based language with macros (and some more stuff).

With Flex, you can directly control the bytes that are added to the resulting binary. Is this something that anyone asked for or wanted? Probably not, but it is fun to toy around with.

With this design the "compiler" (if you can even call it that) has no idea what an ELF is supposed to look like, or what the x86-64 instruction set is.  
*But then how can an executable be created?*  
The program being compiled itself specifies how to build the final executable, so essentially both ELF and x86-64 are implemented as libraries.

In the future I will probably update this to include for details about how the macro system, and the way of outputting the resulting binary.

## Running
Running ``python flex.py [FILES]`` generates an executable `./output` which can be ran on linux.
> Example: ``python flex.py elf.flex x86-64.flex test.flex``
