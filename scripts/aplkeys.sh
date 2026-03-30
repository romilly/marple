#!/bin/bash

if [ "$DISPLAY" >> /dev/null ]
then
        ## We are running Xorg
        if ! [ `setxkbmap -query | awk '/layout/ {print $2}' | grep "apl"` ]
        then
                ## We have no APL layout - so lets set one up - we're going to use the Windows Key.
                ## Setup keyboard map
                XKBRULES=`setxkbmap -query | awk '/rules/ {print $2}'` 2>/dev/null
                XKBMODEL=`setxkbmap -query | awk '/model/ {print $2}'` 2>/dev/null
                XKBLAYOUT=`setxkbmap -query | awk '/layout/ {print $2}'` 2>/dev/null
                XKBVARIANT=`setxkbmap -query | awk '/variant/ {print $2}'` 2>/dev/null
                XKBOPTIONS=`setxkbmap -query | awk '/options/ {print $2}'` 2>/dev/null
                setxkbmap -rules ${XKBRULES} -model ${XKBMODEL} -layout "${XKBLAYOUT},apl" \
                        -variant "${XKBVARIANT},dyalog" \
                        -option "${XKBOPTIONS},grp:win_switch" 2>/dev/null
        fi
fi
