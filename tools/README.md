## Vim Syntax Highlighting

    mkdir -p ~/.vim/syntax
    cp tools/aipl.vim ~/.vim/syntax/aipl.vim
    mkdir -p ~/.vim/ftdetect
    cat > ~/.vim/ftdetect/aipl.vim

    au BufRead,BufNewFile *.aipl set filetype=aipl

Reference: https://vim.fandom.com/wiki/Creating_your_own_syntax_files#Install_the_syntax_file
