if exists("b:current_syntax")
  finish
endif

syntax match aiplComment "^#.*$"

syntax region aiplString start=/^[^!]/ end=/^\ze!/ contained contains=aiplTemplateParameter,aiplComment
syntax match aiplTemplateParameter "{[^}]*}" contained

syn match aiplDef "^!!def\s\+" contained nextgroup=aiplOperatorName
syn match aiplOperatorName "[^ ]\+\n" contained nextgroup=aiplNestedOperator

syntax match aiplCommand "[^ >!][^ >]*" nextgroup=aiplRedirect contained
syntax match aiplOperator /^!\+/ contained nextgroup=aiplCommand contained
syntax match aiplRedirect ">" nextgroup=aiplRedirectTarget contained
syntax match aiplRedirectTarget "[^ >]\+" contained nextgroup=aiplRedirect

syntax region aiplCommandRegion start=/^!/ end=/^\ze!/ contains=aiplOperator,aiplComment,aiplString skipempty

syntax region aiplDefinition start=/^!!def\ze\s/ end="^\ze!" contains=aiplNestedCommandRegion,aiplDef
syntax region aiplNestedCommandRegion start=/^ !/ end=/^\ze \?!/ contained contains=aiplNestedOperator,aiplNestedString,aiplComment skipempty
syntax match aiplNestedOperator /^ !\+/ contained nextgroup=aiplCommand
syntax region aiplNestedString start=/^ [^!]/ end=/^\ze !/ contained contains=aiplTemplateParameter,aiplComment

highlight link aiplComment Comment
highlight link aiplOperator Operator
highlight link aiplNestedOperator Operator
highlight link aiplRedirect Operator
highlight link aiplDef Keyword
highlight link aiplKeyword Keyword
highlight link aiplNestedString String
highlight link aiplString String
highlight link aiplTemplateParameter Identifier

let b:current_syntax = "aipl"
