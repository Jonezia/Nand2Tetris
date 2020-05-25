// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/04/Fill.asm

// Runs an infinite loop that listens to the keyboard input.
// When a key is pressed (any key), the program blackens the screen,
// i.e. writes "black" in every pixel;
// the screen should remain fully black as long as the key is pressed. 
// When no key is pressed, the program clears the screen, i.e. writes
// "white" in every pixel;
// the screen should remain fully clear as long as no key is pressed.

// Put your code here.
//infinite loop:
//    if keyboard is pressed:
//        make screen black
//    else:
//        make screen white

// infinite loop
(INFINITE)
// store value of keyboard in D
@KBD
D=M
// if keyboard is 0, jump to whiten
@WHITEN
D;JEQ
// if not, jump to blacken
@BLACKEN
0;JMP
@INFINITE
0;JMP

(BLACKEN)
// initialise address to SCREEN (16384)
@SCREEN
D=A
@address
M=D
// begin loop1
(LOOP1)
    // get value of address in D
    @address
    D=M
    //check if is equal to 24576, if so then jump to infinite
    @24576
    D=D-A
    @INFINITE
    D;JEQ
    // set 16-bit word at address to all-black
    @address
    A=M
    M=-1
    // increment value of address
    @address
    D=M
    M=D+1
    // jump to loop1
    @LOOP1
    0;JMP
(WHITEN)
// initialise address to SCREEN (16384)
@SCREEN
D=A
@address
M=D
// begin loop2
(LOOP2)
    // get value of address in D
    @address
    D=M
    // check if is equal to 24576, if so then jump to infinite
    @24576
    D=D-A
    @INFINITE
    D;JEQ
    // set 16-bit word at address to all-white
    @address
    A=M
    M=0
    // increment value of address
    @address
    D=M
    M=D+1
    // jump to loop2
    @LOOP2
    0;JMP