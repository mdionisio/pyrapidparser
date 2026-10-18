MODULE files
    ! executed by test_rapid2py.py with standard.sys: text and binary files, directories
    VAR iodev log;
    VAR iodev bin;
    VAR dir folder;
    VAR string line := "";
    VAR string name := "";
    VAR num value := 0;
    VAR num count := 0;
    VAR num data{4} := [72, 105, 10, 255];
    PROC main()
        MakeDir "HOME:/pyrapid_files_test";
        TPWrite "directory " \Bool:=IsFile("HOME:/pyrapid_files_test" \Directory);
        Open "HOME:/pyrapid_files_test/data.txt", log \Write;
        Write log, "first line";
        Write log, "x = " \Num:=12.5;
        Write log, "flag " \Bool:=TRUE \NoNewLine;
        Write log, " and position " \Pos:=[1, 2, 3];
        Write log, "3 4,5";
        Close log;
        TPWrite "size " \Num:=FileSize("HOME:/pyrapid_files_test/data.txt");
        Open "HOME:/pyrapid_files_test/data.txt", log \Read;
        line := ReadStr(log);
        TPWrite "read " + line;
        line := ReadStr(log);
        TPWrite "read " + line;
        line := ReadStr(log);
        TPWrite "read " + line;
        value := ReadNum(log);
        TPWrite "number " \Num:=value;
        value := ReadNum(log \Delim:=",");
        TPWrite "number " \Num:=value;
        value := ReadNum(log \Delim:=",");
        TPWrite "number " \Num:=value;
        line := ReadStr(log);
        TPWrite "end of file " \Bool:=(line = "EOF");
        Rewind log;
        line := ReadStr(log);
        TPWrite "after rewind " + line;
        Close log;
        Open "HOME:/pyrapid_files_test/data.txt", log \Append;
        Write log, "appended";
        Close log;
        Open "HOME:/pyrapid_files_test/data.bin", bin \Bin;
        WriteBin bin, data, 4;
        WriteStrBin bin, "ok";
        Rewind bin;
        value := ReadBin(bin);
        WHILE value <> EOF_BIN DO
            count := count + 1;
            value := ReadBin(bin);
        ENDWHILE
        TPWrite "bytes " \Num:=count;
        Rewind bin;
        line := ReadStrBin(bin, 2);
        TPWrite "binary text " + line;
        Close bin;
        CopyFile "HOME:/pyrapid_files_test/data.txt", "HOME:/pyrapid_files_test/copy.txt";
        RenameFile "HOME:/pyrapid_files_test/copy.txt", "HOME:/pyrapid_files_test/moved.txt";
        TPWrite "moved " \Bool:=IsFile("HOME:/pyrapid_files_test/moved.txt" \RegFile);
        OpenDir folder, "HOME:/pyrapid_files_test";
        WHILE ReadDir(folder, name) DO
            TPWrite "entry " + name;
        ENDWHILE
        CloseDir folder;
        RemoveFile "HOME:/pyrapid_files_test/data.txt";
        RemoveFile "HOME:/pyrapid_files_test/data.bin";
        RemoveFile "HOME:/pyrapid_files_test/moved.txt";
        RemoveDir "HOME:/pyrapid_files_test";
        TPWrite "removed " \Bool:=(NOT IsFile("HOME:/pyrapid_files_test"));
        ! a file that does not exist
        Open "HOME:/pyrapid_files_test/none.txt", log \Read;
        TPWrite "not reached";
    ERROR
        IF ERRNO = ERR_FILEOPEN THEN
            TPWrite "cannot open";
            RETURN;
        ENDIF
        RAISE;
    ENDPROC
ENDMODULE
