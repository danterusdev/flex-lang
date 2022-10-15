macro header ( file_header program_header_instructions program_header_data )
macro file_header ( $0 ( 127:1 "ELF": 2:1 1:1 1:1 3:1 0:1 0:7 2:2 62:2 1:4 4194304+176:8 64:8 0:8 0:4 64:2 56:2 2:2 64:2 0:2 0:2 ) )
macro program_header_instructions ( $0 ( 1:4 5:4 0:8 4194304:8 4194304:8 $1:final_location:8 $1:final_location:8 4096:8 ) )
macro program_header_data ( $0 ( 1:4 4:4 $2:final_offset:8 $2:final_offset+4194304+4096:8 $2:final_offset+4194304+4096:8 $2:final_location:8 $2:final_location:8 4096:8 ) )
alias instruction_location $1
alias data_location $2

macro %string ( push_thing data_location:location+data_location:final_offset+4198400:4 $2 ( %string: ) )

header
