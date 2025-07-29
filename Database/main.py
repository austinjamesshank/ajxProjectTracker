from pathlib import Path
from datetime import date, timedelta
from openai import OpenAI
import os

# py .\Documents\Software\DailyTracking\Database\main.py
    
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GPT_MODEL = "gpt-4.1-nano"

TODAY = date.today()

# --- --- --- ---
# Main 

def main():
    startNewDailyNotes()
    
# --- --- --- ---
# ChatGPT 

def openGptConnection():
    return OpenAI(
        api_key=OPENAI_API_KEY
    )

def promptGpt(gptClient, prompts, shouldPrintResponse=False):
    messages = [
        {"role": "system", "content": "You are a personal assistant for Austin Shank, looking to improve his life."},
        {"role": "user", "content": prompts},
    ]
    response = getGptResponse(gptClient, messages)
    
    if shouldPrintResponse:
        printResponse(response)
    
    return response
    
def getGptResponse(gptClient, inMessages):
    return gptClient.chat.completions.create(
        model=GPT_MODEL,
        messages=inMessages,
        stream=True
    )
    
def printResponse(response):
    for chunk in response:
        if chunk.choices[0].delta.content is not None:
            print(chunk.choices[0].delta.content, end="", flush=True)
    print()
    
# --- --- --- ---
# Note file handling 

def startNewDailyNotes():
    # Gen new notes file
    newFilename = generateNewNotesFile()
    newPath = getNotePath(newFilename)
    # Grab the previous note path
    previousPath = getPreviousNotePath()
    # TODO - if there are no previous notes, prompt the user and get a project list
    # Move notes forward
    moveLinesForward(previousPath, newPath)
    
def getNotePath(filename):
    notesFolder = Path.home() / "Documents" / "Software" / "DailyTracking" / "Notes"
    return notesFolder / filename
    
def generateNewNotesFile():
    return f"{TODAY.isoformat()}.txt"
    
def getPreviousNotePath():
    i = 0
    while i < 100:
        i += 1
        yesterday = TODAY - timedelta(days=i)
        filename = f"{yesterday.isoformat()}.txt"
        filepath = getNotePath(filename)
        if filepath.exists():
            return filepath
    raise FileNotFoundError("No previous notes file found in the last 100 days.")
    
def moveLinesForward(sourcePath, destPath):
    try:
        with open(sourcePath, "r") as sourceFile, open(destPath, "w") as destFile:
            heldLines = {}
            currentSection = ""
            currentSubsection = ""
            for line in sourceFile:
                currentSection, currentSubsection = handleOneLine(destFile,line,currentSection,currentSubsection,heldLines)
        print(f"New notes file: {destFile}.")
    except FileNotFoundError:
        print(f"Error: source file {sourcePath} not found.")
    except IOError as e:
        print(f"IO error: {e}.")
        
def handleOneLine(destFile,line,currentSection,currentSubsection,heldLines):
    strippedLine = line.lstrip()
   
    # Empty line, carry through immediately
    if not strippedLine:
        destFile.write(line)
        return currentSection, currentSubsection

    if isDayCounter(strippedLine):
        handleDayCounter(destFile, line, strippedLine)
        return currentSection, currentSubsection  # These should be null at this point
    # Section headers
    elif isSectionHeader(strippedLine):
        return handleSectionHeader(destFile, line, strippedLine), currentSubsection
    else:
        currentSubsection = handleSectionPiece(destFile, line, strippedLine, currentSubsection, heldLines)
        return currentSection, currentSubsection

def isDayCounter(strippedLine):
    return strippedLine.startswith("~day:")

def handleDayCounter(destFile, line, strippedLine):
    numericDayCount = strippedLine.split(":")[1].strip()
    numericDayCount = int(numericDayCount) + 1
    updatedLine = line.split(":")[0].strip() + f":{numericDayCount}\n"
    handleNewLine(destFile, updatedLine)

def isSectionHeader(strippedLine):
    return strippedLine.startswith("#")

def handleSectionHeader(destFile, line, strippedLine):
    currentSection = strippedLine.strip("#\n").strip()
    handleNewLine(destFile, line)
    return currentSection

def handleSectionPiece(destFile, line, strippedLine, currentSubsection, heldLines):
    # Subsection headers
    if isSubsectionHeader(strippedLine):
        currentSubsection = strippedLine.strip("\n").strip()
        # "Completed" subsection
        if isCompletedSubsection(strippedLine):
            dumpHeldLines(destFile, heldLines, line, "completedActions")
        # "Past Notes" section
        elif isPastNotesSubsection(strippedLine):
            dumpHeldLines(destFile, heldLines, line, "pastNotes")
        else: 
            handleNewLine(destFile, line)
        return currentSubsection
    else:
        # Completed action checkbox 
        if isCompActionItem(strippedLine) and currentSubsection == "Action Items":
            line = line.rstrip("\n") + f" *{(TODAY - timedelta(days=1)).isoformat()}*\n"
            holdLine(heldLines, line, "completedActions")
            return currentSubsection
        # Note item
        elif isNoteItem(strippedLine) and currentSubsection == "Notes":
            holdLine(heldLines, line, "pastNotes")
            return currentSubsection
        # All other lines can be copied directly
        else:
            destFile.write(line)
            return currentSubsection

def holdLine(heldLines, line, key):
    lineDump = getHeldLinesOrCreate(heldLines, key)
    lineDump.append(line)

def dumpHeldLines(destFile, heldLines, line, key):
    lineDump = getHeldLinesOrCreate(heldLines, key)
    handleNewLine(destFile, line)
    for actionLine in lineDump:
        destFile.write(actionLine)
    clearHeldLines(lineDump)

def clearHeldLines(lineDump):
    lineDump.clear()

def getHeldLinesOrCreate(heldLines, key):
    if key not in heldLines:
        heldLines[key] = []
    return heldLines[key]

def handleNewLine(destFile, line):
    if not line.endswith("\n"):
        line += "\n"
    destFile.write(line)

def isSubsectionHeader(strippedLine):
    if strippedLine.startswith("Pinned"):
        return True
    elif strippedLine.startswith("Action Items"):
        return True
    elif strippedLine.startswith("Notes"):
        return True
    elif strippedLine.startswith("Questions"):
        return True
    elif strippedLine.startswith("Completed"):
        return True
    elif strippedLine.startswith("Past Notes"):
        return True
    else:
        return False
    
def isCompletedSubsection(strippedLine):
    return strippedLine.startswith("Completed")
    
def isPastNotesSubsection(strippedLine):
    return strippedLine.startswith("Past Notes")

def isCompActionItem(strippedLine):
    return (strippedLine[0] == "[" and strippedLine[1] == "x" and strippedLine[2] == "]")
    
def isNoteItem(strippedLine):
    return (strippedLine[0] == "-")

# --- --- --- ---        
# END 
    
if __name__ == "__main__":
    main()