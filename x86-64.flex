macro %number:number ( push_instructions ( 104:1 %number:4 ) )

macro push_thing %thing ( push_instructions ( 104:1 %thing ) )

macro syscall ( push_instructions ( 15:1 5:1 ) )
macro syscall0 ( push_instructions ( 88:1 ) syscall )
macro syscall1 ( push_instructions ( 88:1 95:1 ) syscall )
macro syscall2 ( push_instructions ( 88:1 95:1 94:1 ) syscall )
macro syscall3 ( push_instructions ( 88:1 95:1 94:1 90:1 ) syscall )
