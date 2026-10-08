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
@1
    D=A
    @one
    M=D
(CHECK)
    @KBD
    D=M
    @KEY_PRESSED
    D;JNE
    @0
    D=A
    @color
    M=D
    @START_DRAW
    0;JMP
(KEY_PRESSED)
    @color
    M=-1
(START_DRAW)
    @SCREEN
    D=A
    @ptr
    M=D
(DRAW_LOOP)
    @color
    D=M
    @ptr
    A=M
    M=D
    @one
    D=M
    @ptr
    M=D+M
    @ptr
    D=M
    @24576
    D=D-A
    @CHECK
    D;JEQ
    @DRAW_LOOP
    0;JMP