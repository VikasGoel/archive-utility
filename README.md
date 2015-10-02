# Archive Utility
A highly customizable archive utility.  This utility moves files from a source to a target directory.

Source: a directory (absolute or relative), can be a UNC path

Destination: a directory (absolute or relative), can be a UNC path

Actions: Move/Copy/UniqueCopy (defaults to move, UniqueCopy prefixes filenames copied with date/time stamp to ensure files copied are always unique)

Move: Moves the files from the source to the destination. Will move the file to a unique filename if the same file exists already (unique filename is date/timestamp + name of source file)

Copy: Copies files from the source to destination. Copies only files that have a different last modified timestamp than existing files in the destination

UniqueCopy: Copies all files to a unique filename. Filename is date/timestamp + name of source file

Recursion Depth: integer number of levels to recurse (defaults to 0 for none)

Include Pattern: file pattern to include (defaults to '*')

Retention Days: integer number of days to retain files (defaults to 10, use -1 to retain forever)

Encrypt: True/False (defaults to False)
