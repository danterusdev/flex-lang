macro header ( $header:buffer:push ( file_header program_header_instructions program_header_data ) )
macro file_header ( 127:1 "ELF": 2:1 1:1 1:1 3:1 0:1 0:7 2:2 62:2 1:4 4194304+176:8 64:8 0:8 0:4 64:2 56:2 2:2 64:2 0:2 0:2 )
macro program_header_instructions ( 1:4 5:4 0:8 4194304:8 4194304:8 $instructions:buffer:final_location:8 $instructions:buffer:final_location:8 4096:8 )
macro program_header_data ( 1:4 4:4 $header:buffer:final_location+$instructions:buffer:final_location:8 $header:buffer:final_location+$instructions:buffer:final_location+4194304+4096:8 $header:buffer:final_location+$instructions:buffer:final_location+4194304+4096:8 $bss:buffer:final_location:8 $bss:buffer:final_location:8 4096:8 )
alias instruction_location $instructions:buffer:push

macro %string:string ( push_thing $bss:buffer:location+$header:buffer:final_location+$instructions:buffer:final_location+4198400:4 $bss:buffer:push ( %string: ) )

header

final ( write output ( $header:buffer $instructions:buffer $bss:buffer ) )
