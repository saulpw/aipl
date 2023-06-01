if exists("b:current_syntax")
  finish
endif

syn match aiplComment "^#.*$"
syn match aiplOperator "^!\+" nextgroup=aiplCommand
syn match aiplCommand "[^ >]\+" nextgroup=aiplRedirect contained
syn match aiplRedirect ">" nextgroup=aiplRedirectTarget contained
syn match aiplRedirectTarget "[^ >]\+" contained

highlight link aiplComment Comment
highlight link aiplOperator Operator
highlight link aiplRedirect Operator
highlight link aiplRedirectTarget Identifier
highlight link aiplCommand Identifier

let b:current_syntax = "aipl"
