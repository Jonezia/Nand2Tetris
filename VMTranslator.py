# Usage: pass a directory, will parse all the .vm files in the directory into
# an .asm file, containing an assembly version of the virtual machine code
# VM CODE-> ASSEMBLY CODE
import re
import sys
import glob

directory = sys.argv[1]
if directory[-1] == "/":
    directory = directory[:-1]
directoryName = directory[directory.rfind("/")+1:]
files = [f for f in glob.glob(directory + "/*.vm")]
if len(files) is 0:
    print("No .vm files found in this directory")

out_lines = []

def append(value):
    out_lines.append(value)

# Commands to decrement and dereference the stack pointer
def pop():
    for i in ["@SP","M=M-1","@SP","A=M"]:
        append(i)
# Commands to push the value stored in {value} onto the stack, and update the pointer
def push(value):
    for i in ["@SP","A=M",f"M={value}","@SP","M=M+1"]:
        append(i)
def incrementStackPointer():
    append("@SP")
    append("M=M+1")

def arithmeticLogicalCommand(operation):
    # first pop
    pop()
    # Special case: neg & not
    if operation == "neg":
        append("M=-M")
        incrementStackPointer()
        return
    elif operation == "not":
        append("M=!M")
        incrementStackPointer()
        return
    # store the first "pop" in D
    append("D=M")
    # second pop
    pop()
    if operation == "add":
        append("M=D+M")
    elif operation == "sub":
        append("M=M-D")
    elif operation == "and":
        append("M=D&M")
    elif operation == "or":
        append("M=D|M")
    incrementStackPointer()

equalityLabelKey = 0

def equalityCommand(operation):
    global labelKey
    # first pop
    pop()
    # store the first "pop" in D
    append("D=M")
    # second pop
    pop()
    append("D=M-D")
    append(f"@TRUE{equalityLabelKey}")
    append(f"D;J{operation.upper()}")
    push("0") #Add 'false' to stack
    append(f"@END{equalityLabelKey}")
    append("0;JMP")
    append(f"(TRUE{equalityLabelKey})")
    push("-1") #Add 'true' to stack
    append(f"(END{equalityLabelKey})")
    labelKey += 1

segmentPointers={"local": "LCL", "argument": "ARG", "this": "THIS", "that": "THAT"}

def Pcommand(line):
    command, location, value = line.split()
    if location == "constant":
        # Push a constant onto the stack
        append(f"@{value}")
        append("D=A")
        push("D")
    elif location in ["local", "argument", "this", "that"]:
        # Store value in D
        append(f"@{value}")
        append("D=A")
        # Go to pointee of segment pointer
        append(f"@{segmentPointers[location]}")
        # push segment i: addr = segmentPointer + i, *SP = *addr, SP++
        if command == "push":
            # Go to corrent pointee: segmentPointer + i
            append("A=D+M")
            # Store value in D
            append("D=M")
            push("D")
        # pop segment i: addr = segmentPointer + i, SP--, *addr = *SP
        elif command == "pop":
            # Store address in ADDRESS
            append("D=D+M")
            append("@ADDRESS")
            append("M=D")
            pop()
            append("D=M")
            append("@ADDRESS")
            append("A=M")
            append("M=D")
    elif location == "pointer":
        # push: *SP = THIS/THAT (0/1), SP++
        if command == "push":
            if value == "0":
                append("@THIS")
            elif value == "1":
                append("@THAT")
            append("D=M")
            push("D")
        # pop: SP--, THIS/THAT = *SP
        elif command == "pop":
            pop()
            append("D=M")
            if value == "0":
                append("@THIS")
            elif value == "1":
                append("@THAT")
            append("M=D")
    elif location == "temp":
        append("@5")
        append("D=A")
        append(f"@{value}")
        # push: addr = 5+i, *SP = *addr, SP++
        if command == "push":
            # Go to corrent pointee: 5 + i
            append("A=D+A")
            # Store value in D
            append("D=M")
            push("D")
        # pop: addr = 5+i, SP--, *addr = *SP
        elif command == "pop":
            # Store address in ADDRESS
            append("D=D+A")
            append("@ADDRESS")
            append("M=D")
            pop()
            append("D=M")
            append("@ADDRESS")
            append("A=M")
            append("M=D")
    elif location == "static":
        # push: @filename.value, D=M, push(D)
        if command == "push":
            append(f"@{filename}.{value}")
            append("D=M")
            push("D")
        # pop: D = stack.pop(), @filename.value, M=D
        elif command == "pop":
            pop()
            append("D=M")
            append(f"@{filename}.{value}")
            append("M=D")

def ALcommand(line):
    if line in ["eq","lt","gt"]:
        equalityCommand(line)
    else:
    # line in [add, sub, neg, and, or, not]
        arithmeticLogicalCommand(line)

def branchcommand(line):
    command, label = line.split()
    if command == "goto":
        append(f"@{label}")
        append("0;JMP")
    if command == "if-goto":
        pop()
        append("M;JLT")
    if command == "label":
        append(f"({label})")

def command(line):
    append("// " + line)
    words = line.split()
    if len(words) == 1:
        ALcommand(line)
    elif words[0] == "push" or "pop":
        Pcommand(line)
    elif words[0] in ["goto","if-goto","label"]:
        branchcommand(line)

for file in files:
    with open(file,"r") as file_in:
        line = file_in.readline()
        # Empty input file case
        if not line:
            print("Empty input file");
            sys.exit()
        inLineCount = 0
        while line:
            line = line.strip()
            # Checks the line isn't empty or a comment
            if not re.match(r'^\s*$', line) and line[0] != "/":
                if line.find("/") != -1:
                    line = line[:line.find("/")]
                command(line)
                inLineCount += 1
            # Goes to next line
            line = file_in.readline()

file_out = open(directory + "/" + directoryName + "2.asm","w")
file_out.write("")
# Open file again, this time appending lines
file_out = open(directory + "/" + directoryName + "2.asm","a")
for line in out_lines:
    file_out.write(line + "\n")
file_out.close()

print("Successful, " + str(inLineCount) + " lines in, " + str(len(out_lines)) + " lines out")
