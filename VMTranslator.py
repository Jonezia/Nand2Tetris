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
retCounter = 0

def append(value):
    out_lines.append(value)

# Commands to decrement and dereference the stack pointer
def pop():
    for i in ["@SP","M=M-1","A=M"]:
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
    global equalityLabelKey
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
    equalityLabelKey += 1

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
        append("D=M")
        append(f"@{label}")
        append("D;JNE")
    if command == "label":
        append(f"({label})")

def functioncommand(line):
    command, functionName, nArgs = line.split()
    if command == "function":
        # (functionName) (functionName = filename.functionName)
        append(f"({functionName})")
        # repeat nVars times: push 0
        append("@0")
        append("D=A")
        for _ in range(int(nArgs)) :
            push("D")
        pass
    elif command == "call":
        # push returnAddress (retAddr = filename.functionName$ret.i)
        global retCounter
        retCounter += 1
        append(f"@{functionName}$ret.{str(retCounter)}")
        append("D=A")
        push("D")
        # push LCL
        append("@LCL")
        append("D=M")
        push("D")
        # push ARG
        append("@ARG")
        append("D=M")
        push("D")
        # push THIS
        append("@THIS")
        append("D=M")
        push("D")
        # push THAT
        append("@THAT")
        append("D=M")
        push("D")
        # ARG = SP-5-nArgs
        append(f"@{str(int(nArgs)+5)}")
        append("D=A")
        append("@SP")
        append("D=M-D")
        append("@ARG")
        append("M=D")
        # LCL = SP
        append("@SP")
        append("D=M")
        append("@LCL")
        append("M=D")
        # goto functionName
        append(f"@{functionName}")
        append("0;JMP")
        # (returnAddress)
        append(f"({functionName}$ret.{retCounter})")

def dereferenceEndFrameMinusX(x,register):
    for i in [f"@{x}","D=A","@R14","A=M-D","D=M",f"@{register}","M=D"]:
        append(i)

def returncommand(line):
    # endFrame = LCL
    # endFrame stored in temp variable
    append("@LCL")
    append("D=M")
    append("@R14")
    append("M=D")
    # retAddr = *(endFrame - 5)
    # retAddr stored in temp variable
    dereferenceEndFrameMinusX("5","R15")
    # *ARG = pop()
    pop()
    append("D=M")
    append("@ARG")
    append("A=M")
    append("M=D")
    # SP = ARG + 1
    append("@ARG")
    append("D=M+1")
    append("@SP")
    append("M=D")
    # THAT = *(endFrame -1)
    dereferenceEndFrameMinusX("1","THAT")
    # THIS = *(endFrame - 2)
    dereferenceEndFrameMinusX("2","THIS")
    # ARG = *(endFrame - 3)
    dereferenceEndFrameMinusX("3","ARG")
    # LCL = *(endFrame - 4)
    dereferenceEndFrameMinusX("4","LCL")
    # goto retAddr
    append("@R15")
    append("A=M")
    append("0;JMP")

def command(line):
    append("// " + line)
    words = line.split()
    if len(line) <= 3:
        ALcommand(line)
    elif words[0] in ["push","pop"]:
        Pcommand(line)
    elif words[0] in ["goto","if-goto","label"]:
        branchcommand(line)
    elif words[0] in ["function","call"]:
        functioncommand(line)
    elif words[0] in ["return"]:
        returncommand(line)

# Add init code
if len(files) > 1:
    for i in ["@256","D=A","@SP","M=D"]:
        append(i)
    command("call Sys.init 0")

for file in files:
    locator = max(file.rfind("/"),file.rfind("\\"))
    filename = file[locator+1:file.rfind(".")]
    with open(file,"r") as file_in:
        line = file_in.readline()
        # Empty input file case
        if not line:
            print("Empty input file");
            sys.exit()
        inLineCount = 0
        while line:
            # Checks the line isn't empty or a comment
            if not re.match(r'^\s*$', line) and line[0] != "/":
                if line.find("/") != -1:
                    line = line[:line.find("/")]
                line = line.strip()
                command(line)
                inLineCount += 1
            # Goes to next line
            line = file_in.readline()

file_out = open(directory + "/" + directoryName + ".asm","w")
file_out.write("")
# Open file again, this time appending lines
file_out = open(directory + "/" + directoryName + ".asm","a")
for line in out_lines:
    file_out.write(line + "\n")
file_out.close()

print("Successful, " + str(inLineCount) + " lines in, " + str(len(out_lines)) + " lines out")
