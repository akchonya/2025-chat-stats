from chat_loader import load_messages
from stats_time import save_monthly_plot
from stats_words import write_normalized_corpus

msgs = load_messages("result.json")
save_monthly_plot(msgs, "out/monthly_messages.png")
write_normalized_corpus(msgs, "out/normalized_corpus.txt")