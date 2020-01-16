#!/usr/bin/env python36
import sys, os
import argparse
import xml.etree.ElementTree as ET
import pprint
import itertools
import subprocess

# Loads the model specification from a given XML file.
# No need to modify this function - Starter code.
# Writer of this function : Christo Wilson.
def load_model(xml_file):
    try:
        tree = ET.parse(xml_file)
    except:
        print('Error: Unable to parse the given XML file. Perhaps it has a syntax error?')
        sys.exit(-1)  
    root = tree.getroot()
    optional_args = []
    positional_args = []
    opts = root.find('options')
    if opts:
        for opt in opts.iter('option'):
            optional_args.append((opt[0].text, opt[1].text))    
    pos = root.find('positional')
    if pos:
        for arg in pos.iter('arg'):
            positional_args.append(arg[0].text)
    return optional_args, positional_args

# Exit the fuzzer if a non-existant file is passed in as a command line argument.
# No need to modify this function - Starter code.
# Writer of this function : Christo Wilson.
def ensure_file_existence(file_path):
    if not os.path.isfile(file_path):
        print('Error: the file {} does not exist. Please check the path'.format(file_path))
        sys.exit(-1)

# Handle the command line arguments for the fuzzer.
# No need to modify this function.
# Writer of this function : Christo Wilson.
def handle_cmd_line():
    parser = argparse.ArgumentParser()
    parser.add_argument("config")
    parser.add_argument("binary")
    args = parser.parse_args()
    if not args.config.endswith('.xml'):
        print('Error: the first parameter should end in an .xml extension')
        sys.exit(-1)
    ensure_file_existence(args.config)
    ensure_file_existence(args.binary)
    if not os.access(args.binary, os.X_OK):
        print('Error: {} is not executable'.format(args.binary))
        sys.exit(-1)
    return args

# Powerset function creats the powerset from a given list.
def powerset(iterable):
    s = list(iterable)
    return list(itertools.chain.from_iterable(itertools.combinations(s, r) for r in range(len(s)+1)))

# Function adds the optional argument name to each possible value.
def addOption(string, values):
    oldList = []
    for i in range(0, len(values)):
        oldList.append(string)
        oldList.append(values[i])
    newList = list(zip(*[iter(oldList)]*2))
    return newList

# Main prints each bad command line.
def main():
    
    # Puts this in args.config and args.binary.
    args = handle_cmd_line()
    # Load the model specification.
    opts, pargs = load_model(args.config)
    # Declares the test arguments for each type.
    testStrings = ["'", "a", "+", 800*"A",  "/n", "7", "==TRUE"]
    testInts = ["-5", "0", "5", "2000000000000000000000000000000", "5 / 10", "c"]
    # Creates the list of all possible optional and mandatory arguments.
    testPargs = list(itertools.permutations(pargs))
    testOpts = powerset(opts)
    
    # Creates the template test commands.
    templateCommands = []
    for i in range (0, len(testOpts)):
        for j in range (0, len(testPargs)):
            templateCommands.append(testOpts[i])
            templateCommands.append(testPargs[j])
    templateCommands = list(zip(*[iter(templateCommands)]*2))
    
    # Creates the test commands.
    testCommands = []
    for i in range (0, len(templateCommands)):
        temp = []
        current = templateCommands[i]
        for j in range(0, len(current[0])):
            opt = current[0]
            optType = opt[j]
            if optType[1] == 'integer':
                temp.append(addOption(optType[0], testInts))
            elif optType[1] == 'string':
                temp.append(addOption(optType[0], testStrings))
            elif optType[1] == 'null':
                temp.append([optType[0]])
        for z in range(0, len(current[1])):
            parg = current[1]
            if parg[z] == 'integer':
                temp.append(testInts)
            elif parg[z] == 'string':
                temp.append(testStrings)
        testCommands.append(temp)
        
    # Takes the product of the test commands.
    newTestCommands = []
    for i in range(0, len(testCommands)):
        current = testCommands[i]
        newTestCommands.append(list(itertools.product(*current)))

    # This will run the program with the list of optional and mandatory arguments.
    for i in range(0, len(newTestCommands)):
        current = newTestCommands[i]
        for j in range(0, len(current)):
            newCurrent = current[j]
            using = []
            for z in range(0, len(newCurrent)):
                if isinstance(newCurrent[z], str):
                    using.extend([newCurrent[z]])
                else:
                    using.extend(newCurrent[z])
            currentArgs = [args.binary] + using
            try:
                o = subprocess.run(currentArgs, stderr = subprocess.PIPE, stdout = subprocess.PIPE)
                if "Traceback (most recent call last):" in o.stderr.decode() or "Traceback (most recent call last):" in o.stdout.decode():
                    pprint.pprint(using)
            except:
                None
main()

