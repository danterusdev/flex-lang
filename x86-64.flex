macro %number ( instruction_location ( 104:1 %number:4 ) )

macro push_thing %thing ( instruction_location ( 104:1 %thing ) )

macro syscall ( instruction_location ( 15:1 5:1 ) )
macro syscall0 ( instruction_location ( 88:1 ) syscall )
macro syscall1 ( instruction_location ( 88:1 95:1 ) syscall )
macro syscall2 ( instruction_location ( 88:1 95:1 94:1 ) syscall )
macro syscall3 ( instruction_location ( 88:1 95:1 94:1 90:1 ) syscall )
