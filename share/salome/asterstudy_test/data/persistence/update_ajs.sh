#!/bin/bash

update_ajs_create()
{
    local file=$(readlink -f ${1})
    test ! -f ${file} && { echo "Cannot find file '${1}'" ; return ; }
    echo "Updating ${file}"
    local tmpdir=/tmp/tmp${$}
    mkdir -p ${tmpdir}
    local tmpfile=${tmpdir}/$(basename ${file}).ast
    ajs2ast ${file} ${tmpfile}
    ast2ajs ${tmpfile} ${file}
    rm -rf ${tmpdir}
}

update_ajs_main()
{
    local dir=$(readlink -f $(dirname ${0}))
    local file
    for file in ${@:-$(find ${dir} -name "*.ajs")} XXX
    do
	case ${file} in
	    XXX ) continue ;;
	    * ) update_ajs_create ${file} ;;
	esac
    done
}

update_ajs_main "${@}"
