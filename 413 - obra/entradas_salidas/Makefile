all:
	@ruby no_me_quemes.rb 2026-05-01 2026-05-26 | grep -vi propietario | grep -vi profesor

beron:
	@ruby no_me_quemes.rb 2026-05-25 2026-05-31 | egrep -i '(beron|funes)'

beron-semanal:
	@ruby no_me_quemes.rb 2025-12-15 2026-07-31 --group-by "(beron|funes)"

caceres-semanal:
	@ruby no_me_quemes.rb 2026-05-20 2026-06-31 --group-by "(caceres|sergio)"

obra:
	@ruby no_me_quemes.rb 2023-09-01 2025-07-31 | egrep -i '(obrero|material|volquet)'
