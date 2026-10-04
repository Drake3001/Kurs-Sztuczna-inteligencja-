from transformers import AutoConfig

config = AutoConfig.from_pretrained(
    "Voicelab/herbert-base-cased-sentiment"
)

print(config.id2label)
print("siems")