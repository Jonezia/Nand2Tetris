// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/04/Mult.asm

// Multiplies R0 and R1 and stores the result in R2.
// (R0, R1, R2 refer to RAM[0], RAM[1], and RAM[2], respectively.)

// Put your code here.
// This version only works if Ram[1] > 0

// Pseudocode:
// While Ram[1] is not 0:
// 	Ram[2] += Ram[0]
// 	Ram[1] -= 1

// Set Ram[2] to 0, incase Ram[1] is 0
@R2
M=0

(LOOP)
    // If Ram[1] is 0, jump to end
    // select Ram[1] and put value in D
    @R1
    D=M
    // If D is 0, jump to end
    @END
    D;JEQ

    // Ram[2] += Ram[0]
    // Put value of Ram[0] in D
    @R0
    D=M
    // Put value of Ram[2] in A
    @R2
    A=M
    // Put sum of Ram[0] and Ram[2] in D
    D=D+A
    // Select Ram[2] and set its value to D
    @R2
    M=D

    // Ram[1] -= 1
    @R1
    // Store value of Ram[1] in D
    D=M
    // Select Ram[1], set its value to D-1
    @R1
    M=D-1

    // Jump to loop unconditionally
    @LOOP
    0;JMP

// Infinite loop
(END)
@END
0;JMP
