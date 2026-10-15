# MiniGPT student working copy

Follow Mentor Liu's Week 2 tasks. Edit only the four forward methods in model.py
when prompted: AttentionHead, MultiHeadAttention, FeedForward and TransformerBlock.
Write your own small code attempt in chat; the mentor saves it and runs the next
relevant check. Ask for a hint or a numerical example if a concept is unfamiliar.

The four TODOs are intentional. No completed instructor model is installed here.
Data contains synthetic English logs, not real industrial measurements. The
96-character vocabulary is fixed and the training/validation records are separate.

The local transformer-map.html shows the original architecture image beside an
English module/code guide. It needs no internet connection. It explains important
differences between the 2017 encoder-decoder figure and this Pre-LN decoder model.

seminar_step.py is the recorded experiment adapter. Other scripts contain the
data, tests, training, measurement,
plotting and deliberate failure experiments. Result JSON/CSV/PNG files live in the
run folders linked by the progress helper, not inside the distributed plugin.
Core comparison: one run per device. Three repetitions and full Batch scanning
are optional. Keep all actual outputs, including failed tests and unavailable GPUs.
