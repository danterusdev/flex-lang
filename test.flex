macro print ( $type_stack:stack:pop_check ( string "String expected": ) $type_stack:stack:pop_check ( integer "integer expected": ) 1 sys_write )

macro %number:number ( $type_stack:stack:push ( integer ) )
macro %string:string ( $type_stack:stack:push ( string ) )

1 1 print
4 "test" print
0 sys_exit
