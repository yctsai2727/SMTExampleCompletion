#!/bin/bash
# AUTHORS: Guillermo A. Perez + Philipp Meyer
# DESCRIPTION: The post-processor for synthesis tools on .tlsf benchmarks
#              (Based on Jens Kreber's script). This version of the post-
#              processor uses nuXMV to model check synthesized controllers.
# arg1 = the absolute path to the benchmark file (.tlsf)
# - modified to call acacia-bonsai


BASE=$(dirname "$0")
cd $BASE
TESTFOLDER=$(mktemp -d)

syntf="$TESTFOLDER/synthesis.aag"
origf="$1"
abpath="$2"

# convert TLSF to LTL formula + inputs/outputs
FORMULA=$(./meyerphi-syfco "$origf" -f ltlxba-decomp -m fully)

# return if the file is not found -> error
RET=$?
if [ $RET -ne 0 ]; then
    exit -1
fi


INPS=$(./meyerphi-syfco "$origf" -f ltlxba-decomp -ins)
OUTPS=$(./meyerphi-syfco "$origf" -f ltlxba-decomp -outs)
# get rid of spaces: a, b, c -> a,b,c
INPS=$(sed 's/ //g' <<< "$INPS")
OUTPS=$(sed 's/ //g' <<< "$OUTPS")

FORMULA=$(sed ':a;N;$!ba;s/\n/" -f "/g' <<< "$FORMULA")
#FORMULA="-f \"$FORMULA\""

echo "$abpath/src/acacia-bonsai -f \"$FORMULA\" --ins \"$INPS\" --outs \"$OUTPS\" -S \"$syntf\" --check=real"
# call acacia-bonsai to do synthesis
eval "$abpath/src/acacia-bonsai -f \"$FORMULA\" --ins \"$INPS\" --outs \"$OUTPS\" -S \"$syntf\" --check=real"
#ltlsynt -f "$FORMULA" --ins="$INPS" --outs="$OUTPS" --aiger | sed '1d' > "$syntf"
#ltlsynt --tlsf="$origf" --aiger | sed '1d' > "$syntf"

if [[ -f "$syntf" ]]; then
    echo Synthesis seems to be ok?
else
    echo No synthesis!
    exit -1
fi

./process-modelcheck.sh "$syntf" "$origf" "$TESTFOLDER"
CODE=$?
rm -r "$TESTFOLDER"
echo modelcheck: code $CODE
exit $CODE
