#!/bin/zsh
# Doppio clic dal Finder: aggiunge un iscritto alla newsletter (vedi scripts/add_subscriber.py).
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"
export LANG="${LANG:-it_IT.UTF-8}"
cd "$(dirname "$0")/.." || exit 1
python3 scripts/add_subscriber.py "$@"
code=$?
echo
if [ $code -eq 0 ]; then
  echo "Fatto. Puoi chiudere questa finestra."
else
  echo "Uscito con codice $code. Puoi chiudere questa finestra."
fi
exit $code
