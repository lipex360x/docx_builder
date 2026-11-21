on run argv
  if (count of argv) is not 2 then error "Pass an absolute document path and filename."
  set targetPath to item 1 of argv
  set targetName to item 2 of argv
  if application "Microsoft Word" is not running then return "NOT_OPEN"
  tell application "Microsoft Word"
    set openDocuments to every document
    repeat with targetDoc in openDocuments
      if name of targetDoc is targetName then
        set documentPath to POSIX path of ((full name of targetDoc) as alias)
        if documentPath is targetPath then
          if saved of targetDoc then
            set outputLines to {"Status: saved"}
          else
            set outputLines to {"Status: unsaved changes"}
          end if
          set targetComments to every Word comment of targetDoc
          set end of outputLines to "Comments: " & (count of targetComments)
          repeat with targetComment in targetComments
            set end of outputLines to "Author: " & (author of targetComment)
            set end of outputLines to "Selected text: " & (content of scope of targetComment)
            set end of outputLines to "Comment: " & (content of comment text of targetComment)
          end repeat
          set AppleScript's text item delimiters to linefeed
          return outputLines as text
        end if
      end if
    end repeat
  end tell
  return "NOT_OPEN"
end run
