# Usage: pass a directory, will parse all the .jack files in the directory into vm code (.vml files)

import re
import sys
import glob

class Reader:
    def __init__(self, file):
        self.inLineCount = 0
        self.blockComment = False
        locator = max(file.rfind("/"),file.rfind("\\"))
        self.filename = file[locator+1:file.rfind(".")]
        self.file_in = open(file,"r")
        # Set up tokens file
        self.tokens_out = open(directory + "/_" + self.filename + "T.xml","w")
        self.tokens_out.write("")
        # Open file again, this time appending lines
        self.tokens_out = open(directory + "/_" + self.filename + "T.xml","a")
        # Set up XML output file
        self.file_out = open(directory + "/_" + self.filename + ".xml","w")
        self.file_out.write("")
        # Open file again, this time appending lines
        self.file_out = open(directory + "/_" + self.filename + ".xml","a")
        # Set up vm output file
        self.vm_out = open(directory + "/_" + self.filename + ".vm","w")
        self.vm_out.write("")
        # Open file again, this time appending lines
        self.vm_out = open(directory + "/_" + self.filename + ".vm","a")
        self.tokenizer = Tokenizer(self.tokens_out)

    def run(self):
        line = self.file_in.readline()
        if not line:
            self.endOfFile()
        else:
            line = line.strip()
            if not line == "" and not line.startswith("//"):
                if self.blockComment == False:
                    if line.startswith("/*"):
                        self.blockComment = True
                    else:
                        if line.find("//") != -1:
                            line = line[:line.find("//")]
                        self.inLineCount += 1
                        self.tokenizer.tokenize(line)
                if line.endswith("*/"):
                    self.blockComment = False
            self.run()

    def endOfFile(self):
        self.file_in.close()
        self.tokens_out.write("</tokens>")
        self.tokens_out.close()
        self.parser = Parser(self.file_out,self.vm_out,self.tokenizer.tokens)
        self.parser.parseClass()


class Tokenizer:
    # Breaks each line into tokens
    def __init__(self,tokens_out):
        self.num_tokens = 0
        self.tokens = []
        self.tokens_out = tokens_out
        self.tokens_out.write("<tokens>\n")

    def tokenize(self,line):
        string = []
        # split by whitespace and symbols
        tempTokens = re.split("([\s\[\{\}\(\)\[\]\.\*\+\|\-,;/&<>=~])",line)
        tempTokens = [token for token in tempTokens if not token.strip() == ""]
        for token in tempTokens:
            # If we are processing a string
            if len(string) > 0:
                if token.endswith("\""):
                    string.append(token[:-1])
                    outString = " ".join(string)
                    self.add_token("stringConstant",outString)
                    string = []
                else:
                    string.append(token)
            else:
                if token.startswith("\""):
                    # If token is a complete string
                    if token.endswith("\""):
                        self.add_token("stringConstant",token[1:-1])
                    else:
                        string.append(token[1:])
                        continue
                elif token in ["class","constructor","function","method","field",
                "static","var","int","char","boolean","void","true","false",
                "null","this","let","do","if","else","while","return"]:
                    self.add_token("keyword",token)
                elif token in ["{","}","(",")","[","]",".",",",";","+","-","*",
                "/","&","|","<",">","=","~"]:
                    if token == "&":
                        self.add_token("symbol","&amp;")
                    elif token == "<":
                        self.add_token("symbol","&lt;")
                    elif token == ">":
                        self.add_token("symbol","&gt;")
                    else:
                        self.add_token("symbol",token)
                elif token.isdigit():
                    self.add_token("integerConstant",token)
                else:
                    self.add_token("identifier",token)

    def add_token(self,tokenType,tokenName):
        self.num_tokens += 1
        self.tokens_out.write(f"<{tokenType}>{tokenName}</{tokenType}>\n")
        self.tokens.append([tokenType,tokenName])

class Parser:
    # Parses tokens into xml tree
    def __init__(self,file_out,vm_out,tokens):
        self.file_out = file_out
        self.vm_out = vm_out
        self.pointer = 0
        self.subroutine_args = 0
        self.label_number = 0
        self.symbolTable = SymbolTable()
        self.currentTokenType = None
        self.currentTokenName = None
        self.currentClass = None
        self.currentSubroutine = None
        self.tokens = tokens
        self.get_next_token()

    def get_next_token(self):
        if self.pointer != len(self.tokens) - 1:
            self.currentTokenType, self.currentTokenName = self.tokens[self.pointer]
            self.pointer += 1
            return self.currentTokenType,self.currentTokenName

    def lookfor(self,mode,name,type,errMessage = False):
        if mode == "name":
            if self.currentTokenName == name:
                self.add_token(self.currentTokenType,name)
            else:
                if errMessage:
                    self.error_message(errMessage)
        elif mode == "type":
            if self.currentTokenType == type:
                self.add_token(type,self.currentTokenName)
            else:
                if errMessage:
                    self.error_message(errMessage)
        self.get_next_token()

    def parseClass(self):
        # 'class' className '{' classVarDec* subroutineDec* '}'
        if self.currentTokenName == "class":
            self.file_out.write("<class>\n")
            self.add_token("keyword","class")
            self.get_next_token()
            self.currentClass = self.currentTokenName
            self.lookfor("type",None,"identifier","className identifier in " +
            "class declaration")
            self.lookfor("name","{",None,"{ in class declaration")
            while True:
                if not self.parseClassVarDec():
                    break
            while True:
                if not self.parseSubroutineDec():
                    break
            self.lookfor("name","}",None,"} in class declaration")
            self.file_out.write("</class>\n")
            self.get_next_token()
            return True
        else:
            return False

    def parseClassVarDec(self):
        # ('static' | 'field') type varName (',' varName)* ';'
        if self.currentTokenName in ["static","field"]:
            kind = self.currentTokenName
            self.file_out.write("<classVarDec>\n")
            self.add_token("keyword",self.currentTokenName)
            self.get_next_token()
            # type: 'int' | 'char' | 'boolean' | className
            # className: identifier
            type = self.currentTokenName
            if self.currentTokenType == "identifier":
                self.add_token("identifier",self.currentTokenName)
            elif self.currentTokenName in ["int","char","boolean"]:
                self.add_token("keyword",self.currentTokenName)
            else:
                self.error_message("Expected type in class variable declaration")
            self.get_next_token()
            # varName: identifier
            self.symbolTable.define(self.currentTokenName,type,kind)
            self.lookfor("type",None,"identifier","variable name identifier " +
            "in class variable declaration")
            # (',' varName)* ';'
            while self.currentTokenName == ",":
                self.add_token("symbol",",")
                self.get_next_token()
                self.symbolTable.define(self.currentTokenName,type,kind)
                self.lookfor("type",None,"identifier","variable name " +
                "identifier after comma in class variable declaration")
            self.lookfor("name",";",None,"; after class variable declaration")
            self.file_out.write("</classVarDec>\n")
            return True
        else:
            return False

    def lookfortype(self,void,errMessage):
        # helper function to parse (type)
        if void:
            if self.currentTokenType == "identifier":
                self.add_token("identifier",self.currentTokenName)
            elif self.currentTokenName in ["int","char","boolean","void"]:
                self.add_token("keyword",self.currentTokenName)
            else:
                self.error_message("Expected type or void " + errMessage)
        else:
            if self.currentTokenType == "identifier":
                self.add_token("identifier",self.currentTokenName)
            elif self.currentTokenName in ["int","char","boolean"]:
                self.add_token("keyword",self.currentTokenName)
            else:
                self.error_message("Expected type " + errMessage)
        self.get_next_token()

    def parseSubroutineDec(self):
        # ('constructor' | 'function' | 'method') ('void' | type) subroutineName
        # '(' parameterList ')' subroutineBody
        functionType = self.currentTokenName
        if functionType in ["constructor","function","method"]:
            self.file_out.write("<subroutineDec>\n")
            self.symbolTable.startSubroutine()
            self.label_number = 0
            self.symbolTable.define("this",self.currentClass,"arg")
            self.add_token("keyword",self.currentTokenName)
            self.get_next_token()
            # ('void' | type)
            # type: 'int' | 'char' | 'boolean' | className className: identifier
            self.lookfortype(True,"in subroutine declaration")
            # subroutineName: identifier
            self.currentSubroutine = self.currentTokenName
            self.lookfor("type",None,"identifier","subroutine name " +
            "identifier in subroutine declaration")

            self.vm_out.write("function " + self.currentClass + "." + self.currentSubroutine
            + " " + str(self.symbolTable.varCount + self.symbolTable.staticCount) + "\n")

            # '(' parameterList ')'
            self.lookfor("name","(",None,"( in subroutine declaration")
            self.parseParameterList()
            self.lookfor("name",")",None,") in subroutine declaration")
            # subroutineBody: '{' varDec* statements '}'
            self.file_out.write("<subroutineBody>\n")
            self.lookfor("name","{",None,"{ in subroutine declaration")
            while True:
                if not self.parseVarDec():
                    break
            self.parseStatements()
            self.lookfor("name","}",None,"} in subroutine declaration")

            if functionType == "constructor":
                self.vm_out.write("push constant " + self.symbolTable.fieldCount + "\n")
                self.vm_out.write("call Memory.alloc 1" + "\n")
                self.vm_out.write("pop pointer 0" + "\n")
            elif functionType == "method":
                self.vm_out.write("push argument 0" + "\n")
                self.vm_out.write("pop pointer 0" + "\n")

            self.file_out.write("</subroutineBody>\n")
            self.file_out.write("</subroutineDec>\n")
            return True
        else:
            return False

    def parseParameterList(self):
        # ((type varName)(',' type varName)*)?
        self.file_out.write("<parameterList>\n")
        if self.currentTokenType == "identifier" or self.currentTokenName \
        in ["int","char","boolean"]:
            # (type varName) varName: identifier
            type = self.currentTokenName
            self.lookfortype(False,"in parameter list")
            self.symbolTable.define(self.currentTokenName,type,"arg")
            self.lookfor("type",None,"identifier","varName identifier in parameter list")
            # (',' type varName)* varName: identifier
            while self.currentTokenName == ",":
                self.add_token("symbol",",")
                self.get_next_token()
                type = self.currentTokenName
                self.lookfortype(False,"in parameter list after ,")
                self.symbolTable.define(self.currentTokenName,type,"arg")
                self.lookfor("type",None,"identifier","varName identifier " +
                "after comma in parameter list")
        self.file_out.write("</parameterList>\n")

    def parseVarDec(self):
        # 'var' type varName (',' varName)* ';'
        if self.currentTokenName == "var":
            self.file_out.write("<varDec>\n")
            self.add_token("keyword","var")
            self.get_next_token()
            type = self.currentTokenName
            self.lookfortype(False,"in variable declaration")
            self.symbolTable.define(self.currentTokenName,type,"var")
            self.lookfor("type",None,"identifier","varName identifer in " +
            "variable declaration")
            while self.currentTokenName == ",":
                self.add_token("symbol",",")
                self.get_next_token()
                self.symbolTable.define(self.currentTokenName,type,"var")
                self.lookfor("type",None,"identifier","varName identifier " +
                "after comma in variable declaration")
            self.lookfor("name",";",None,"semicolon after variable declaration")
            self.file_out.write("</varDec>\n")
            return True
        else:
            return False

    def parseStatements(self):
        # statement*
        # statement: letStatement | if statement | whileStatement | doStatement
        # returnStatement
        self.file_out.write("<statements>\n")
        while True:
            if not self.parseStatement():
                break
        self.file_out.write("</statements>\n")

    def parseStatement(self):
        # helper function for parseStatements
        if self.parseLetStatement():
            return True
        elif self.parseIfStatement():
            return True
        elif self.parseWhileStatement():
            return True
        elif self.parseDoStatement():
            return True
        elif self.parseReturnStatement():
            return True
        else:
            return False

    def parseLetStatement(self):
        # 'let' varName ('[' expression ']')? '=' expression ';'
        if self.currentTokenName == "let":
            self.file_out.write("<letStatement>\n")
            self.add_token("keyword","let")
            self.get_next_token()
            leftoperand = self.currentTokenName
            self.lookfor("type",None,"identifier","varName identifier after let")
            if self.currentTokenName == "[":
                self.add_token("symbol","[")
                self.get_next_token()
                self.parseExpression()
                self.vm_out.write("push " + self.symbolTable.getVM(leftoperand) + "\n")
                self.vm_out.write("add" + "\n")
                self.lookfor("name","]",None,"] after [ in let statement]")
                self.lookfor("name","=",None,"= in let statement")
                self.parseExpression()
                self.vm_out.write("pop temp 0" + "\n")
                self.vm_out.write("pop pointer 1" + "\n")
            else:
                self.lookfor("name","=",None,"= in let statement")
                self.parseExpression()
                self.vm_out.write("pop " + self.symbolTable.getVM(leftoperand) + "\n")
            self.lookfor("name",";",None,"; after let statement")
            self.file_out.write("</letStatement>\n")
            return True
        else:
            return False

    def get_labels(self):
        L1 = self.currentClass + "." + self.currentSubroutine + "." + \
            str(self.label_number) + ".1"
        L2 = self.currentClass + "." + self.currentSubroutine + "." + \
            str(self.label_number) + ".2"
        self.label_number += 1
        return L1, L2

    def parseIfStatement(self):
        # 'if' '(' expression ')' '{' statements '}' ('else' '{' statements '}')?
        L1, L2 = self.get_labels()
        if self.currentTokenName == "if":
            self.file_out.write("<ifStatement>\n")
            self.add_token("keyword","if")
            self.get_next_token()
            self.lookfor("name","(",None,"( in if statement)")
            self.parseExpression()
            self.lookfor("name",")",None,") in if statement")
            self.vm_out.write("not" + "\n")
            self.vm_out.write("if-goto " + L1 + "\n")
            self.lookfor("name","{",None,"{ in if statement")
            self.parseStatements()
            self.vm_out.write("goto " + L2 + "\n")
            self.vm_out.write("label " + L1 + "\n")
            self.lookfor("name","}",None,"} in if statement")
            if self.currentTokenName == "else":
                self.add_token("keyword","else")
                self.get_next_token()
                self.lookfor("name","{",None,"{ after else in if statement")
                self.parseStatements()
                self.lookfor("name","}",None,"} after else in if statement")
            self.vm_out.write("label " + L2 + "\n")
            self.file_out.write("</ifStatement>\n")
            return True
        else:
            return False

    def parseWhileStatement(self):
        # 'while' '(' expression ')' '{' statements '}'
        L1, L2 = self.get_labels()
        if self.currentTokenName == "while":
            self.file_out.write("<whileStatement>\n")
            self.add_token("keyword","while")
            self.get_next_token()
            self.vm_out.write("label " + L1 + "\n")
            self.lookfor("name","(",None,"( in while statement")
            self.parseExpression()
            self.vm_out.write("not" + "\n")
            self.vm_out.write("if-goto " + L2 + "\n")
            self.lookfor("name",")",None,") in while statement")
            self.lookfor("name","{",None,"{ in while statement")
            self.parseStatements()
            self.vm_out.write("goto " + L1 + "\n")
            self.vm_out.write("label " + L2 + "\n")
            self.lookfor("name","}",None,"} in while statement")
            self.file_out.write("</whileStatement>\n")
            return True
        else:
            return False

    def parseSubroutineCall(self,location,name=None):
        # helper function for parseDoStatement and parseTerm
        self.subroutine_args = 0
        if self.currentTokenName == ".":
            # className or varName
            if self.symbolTable.getEntry(name):
                # varName
                type, kind, number = self.symbolTable.get(name)
                self.vm_out.write("push " + kind + " " + number)
                self.subroutine_args += 1
                call_prefix = type
            else:
                # className
                call_prefix = name
            self.add_token("symbol",".")
            self.get_next_token()
            call_name = call_prefix + "." + self.currentTokenName
            self.lookfor("type",None,"identifier","subroutineName identifier " +
            "after . in do statement")
        else:
            # subroutineName
            self.vm_out.write("push pointer 0")
            self.subroutine_args += 1
        self.lookfor("name","(",None,"( in " + location)
        self.parseExpressionList()
        self.lookfor("name",")",None,") after ( in " + location)
        self.vm_out.write("call " + call_name + " " + str(self.subroutine_args) + "\n")

    def parseDoStatement(self):
        # 'do' subroutineCall ';'
        # subroutineCall: subroutineName '(' expressionList ')' | (className |
        # varName) '.' subroutineName '(' expressionList ')'
        # subroutineName, varName, className: identifier
        if self.currentTokenName == "do":
            self.file_out.write("<doStatement>\n")
            self.add_token("keyword","do")
            self.get_next_token()
            # subroutine call
            name = self.currentTokenName
            self.lookfor("type",None,"identifier","subroutineName, className " +
            "or varName identifier in do statement")
            self.parseSubroutineCall("do statement",name)
            self.lookfor("name",";",None,"; after do statement")
            self.file_out.write("</doStatement>\n")
            return True
        else:
            return False

    def parseReturnStatement(self):
        # 'return' expression? ';'
        void = True
        if self.currentTokenName == "return":
            self.file_out.write("<returnStatement>\n")
            self.add_token("keyword","return")
            self.get_next_token()
            if self.currentTokenType in ["integerConstant","stringConstant", \
            "identifier"] or self.currentTokenName in ["true","false","null", \
            "this","(","-","~"]:
                void = False
                self.parseExpression()
            if void:
                self.vm_out.write("push constant 0" + "\n")
            self.vm_out.write("return" + "\n")
            self.lookfor("name",";",None,"; after return statement")
            self.file_out.write("</returnStatement>\n")
            return True
        else:
            return False

    def parseExpression(self):
        # term (op term)*
        # op: '+', '-', '*', '/', '&', '|', '<', '>', '='
        self.file_out.write("<expression>\n")
        if self.parseTerm():
            while self.currentTokenName in ["+","-","*","/","&amp;","|","&lt;","&gt;","="]:
                operator = self.currentTokenName
                self.add_token("symbol",self.currentTokenName)
                self.get_next_token()
                self.parseTerm()
                if operator == "*":
                    self.vm_out.write("call Math.multiply 2" + "\n")
                elif operator == "/":
                    self.vm_out.write("call Math.divide 2" + "\n")
                else:
                    op_dict = {'+':'add','-':'sub','=':'eq','&gt;':'gt',
                    '&lt;':'lt','&amp':'and','|':'or'}
                    self.vm_out.write(op_dict[operator] + "\n")
            self.file_out.write("</expression>\n")
            return True
        else:
            self.file_out.write("</expression>\n")
            return False

    def parseTerm(self):
        # integerConstant | stringConstant | keywordConstant | varName |
        # varName '[' expression ']' | subroutineCall | '(' expression ')' |
        # unaryOp term

        # keywordConstant: 'true' | 'false' | 'null' | 'this'
        # unaryOp: '-', '~'
        # subroutineCall: subroutineName '(' expressionList ')' | (className |
        # varName) '.' subroutineName '(' expressionList ')'
        self.file_out.write("<term>\n")
        if self.currentTokenType == "integerConstant":
            self.vm_out.write("push constant " + self.currentTokenName + "\n")
            self.add_token(self.currentTokenType,self.currentTokenName)
            self.get_next_token()
            self.file_out.write("</term>\n")
            return True
        elif self.currentTokenType == "stringConstant":
            string = self.currentTokenName
            self.vm_out.write("push constant " + str(len(string)) + "\n")
            self.vm_out.write("call String.new 1" + "\n")
            for i in string:
                self.vm_out.write("push constant " + str(ord(i)) + "\n")
                self.vm_out.write("call String.appendChar 2" + "\n")
            self.add_token(self.currentTokenType,self.currentTokenName)
            self.get_next_token()
            self.file_out.write("</term>\n")
            return True
        elif self.currentTokenName in ["true","false","null","this"]:
            if self.currentTokenName == "true":
                self.vm_out.write("push constant -1" + "\n")
            elif self.currentTokenName == "false":
                self.vm_out.write("push constant 0" + "\n")
            elif self.currentTokenName == "null":
                self.vm_out.write("push constant 0" + "\n")
            elif self.currentTokenName == "this":
                self.vm_out.write("push pointer 0" + "\n")
            self.add_token("keyword",self.currentTokenName)
            self.get_next_token()
            self.file_out.write("</term>\n")
            return True
        elif self.currentTokenType == "identifier":
            currentName = self.currentTokenName
            currentVM = self.symbolTable.getVM(self.currentTokenName)
            self.add_token("identifier",self.currentTokenName)
            self.get_next_token()
            if self.currentTokenName == "[":
                self.add_token("symbol","[")
                self.get_next_token()
                self.parseExpression()
                self.lookfor("name","]",None,"] after [ in term")
                self.vm_out.write("push " + currentVM + "\n")
                self.vm_out.write("add" + "\n")
                self.vm_out.write("pop pointer 1" + "\n")
                self.vm_out.write("push that 0" + "\n")
            elif self.currentTokenName in ["(","."]:
                self.parseSubroutineCall("term",currentName)
            else:
                self.vm_out.write("push " + currentVM + "\n")
            self.file_out.write("</term>\n")
            return True
        elif self.currentTokenName == "(":
            self.add_token("symbol","(")
            self.get_next_token()
            self.parseExpression()
            self.lookfor("name",")",None,"expected ) after expression in term")
            self.file_out.write("</term>\n")
            return True
        elif self.currentTokenName in ["-","~"]:
            self.vm_out.write("push " + currentVM + "\n")
            if self.currentTokenName == "-":
                self.vm_out.write("neg" + "\n")
            elif self.currentTokenName == "~":
                self.vm_out.write("not" + "\n")
            self.add_token("symbol",self.currentTokenName)
            self.get_next_token()
            self.parseTerm()
            self.file_out.write("</term>\n")
            return True
        else:
            self.file_out.write("</term>\n")
            return False

    def parseExpressionList(self):
        # (expression (',' expression)*)?
        self.file_out.write("<expressionList>\n")
        if self.currentTokenType in ["integerConstant","stringConstant", \
        "identifier"] or self.currentTokenName in ["true","false","null", \
        "this","(","-","~"]:
            self.parseExpression()
            self.subroutine_args += 1
            while self.currentTokenName == ",":
                self.add_token("symbol",",")
                self.get_next_token()
                self.parseExpression()
                self.subroutine_args += 1
            self.file_out.write("</expressionList>\n")
            return True
        else:
            self.file_out.write("</expressionList>\n")
            return False

    def error_message(self,message):
        print("expected " + message + " token " + str(self.pointer))

    def add_token(self,tokenType,tokenName):
        self.file_out.write(f"<{tokenType}>{tokenName}</{tokenType}>\n")

class SymbolTable:
    def __init__(self):
        self.fieldCount = 0
        self.staticCount = 0
        self.argCount = 0
        self.varCount = 0
        self.classSymbolTable = {}
        self.subroutineSymbolTable = {}

    def startSubroutine(self):
        self.argCount = 0
        self.varCount = 0
        self.subroutineSymbolTable = {}

    def define(self,name,type,kind):
        if kind in ["field","static"]:
            self.classSymbolTable[name] = [type,kind,self.getCount(kind)]
        elif kind in ["arg","var"]:
            self.subroutineSymbolTable[name] = [type,kind,self.getCount(kind)]
        self.incrementCount(kind)

    def getEntry(self,name):
        if name in self.subroutineSymbolTable:
            return self.subroutineSymbolTable[name]
        elif name in self.classSymbolTable:
            return self.classSymbolTable[name]
        else:
            return False

    def getVM(self,name):
        var = self.getEntry(name)
        if not var:
            return False
        if var[1] == "field":
            kind = "this"
        elif var[1] == "static":
            kind = "static"
        elif var[1] == "arg":
            kind = "argument"
        elif var[1] == "var":
            kind = "local"
        return(kind + " " + str(var[2]))

    def getCount(self,kind):
        if kind == "field":
            return self.fieldCount
        elif kind == "static":
            return self.staticCount
        elif kind == "arg":
            return self.argCount
        elif kind == "var":
            return self.varCount

    def incrementCount(self,kind):
        if kind == "field":
            self.fieldCount += 1
        elif kind == "static":
            self.staticCount += 1
        elif kind == "arg":
            self.argCount += 1
        elif kind == "var":
            self.varCount += 1

# Main
directory = sys.argv[1]
if directory[-1] == "/":
    directory = directory[:-1]
files = [f for f in glob.glob(directory + "/*.jack")]
if len(files) is 0:
    print("No .jack files found in this directory")
else:
    for file in files:
        jackAnalyser = Reader(file)
        jackAnalyser.run()
        print(jackAnalyser.filename + " successful, " + str(jackAnalyser.inLineCount) +
        " lines in, " + str(jackAnalyser.tokenizer.num_tokens) + " tokens generated")
