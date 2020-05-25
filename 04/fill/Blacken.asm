//ASM Script that blackens the screen

//initialise address to SCREEN (16384)
@SCREEN
D=A
@address
M=D
//begin loop
(LOOP)
    //get value of address in D
    @address
    D=M
    //check if is equal to 24576, if so then jump to end
    @24576
    D=D-A
    @END
    D;JEQ
    //set 16-bit word at address to all-black
    @address
    A=M
    M=-1
    //increment value of address
    @address
    D=M
    M=D+1
    //jump to loop
    @LOOP
    0;JMP
//infinite loop
(END)
@END
0;JMP