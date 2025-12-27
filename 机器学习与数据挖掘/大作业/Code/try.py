import torch
import torch.nn as nn
import torch.optim as optim
from transformers import GPT2Tokenizer
from torch.utils.data import DataLoader, Dataset
import logging
import os


class GPT(nn.Module):
    def __init__(self, vocab_size, d_model=512, nhead=8, num_layers=6, dim_feedforward=2048):
        super(GPT, self).__init__()
        self.embedding = nn.Embedding(vocab_size, d_model)
        self.pos_encoder = PositionalEncoding(d_model)
        # 设置 batch_first 为 True
        encoder_layer = nn.TransformerEncoderLayer(d_model, nhead, dim_feedforward, batch_first=True)
        self.transformer_encoder = nn.TransformerEncoder(encoder_layer, num_layers)
        self.lm_head = nn.Linear(d_model, vocab_size)

    def forward(self, src):
        src = self.embedding(src)
        src = self.pos_encoder(src)
        output = self.transformer_encoder(src)
        output = self.lm_head(output)
        return output


class PositionalEncoding(nn.Module):
    def __init__(self, d_model, dropout=0.1, max_len=5000):
        super(PositionalEncoding, self).__init__()
        self.dropout = nn.Dropout(p=dropout)
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-torch.log(torch.tensor(10000.0)) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0).transpose(0, 1)
        self.register_buffer('pe', pe)

    def forward(self, x):
        x = x + self.pe[:x.size(0), :]
        return self.dropout(x)


class TextDataset(Dataset):
    def __init__(self, tokenizer, file_path, block_size=128):
        self.tokenizer = tokenizer
        self.block_size = block_size
        self.examples = []
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        tokenized_text = tokenizer.encode(text)
        for i in range(0, len(tokenized_text) - block_size + 1, block_size):
            self.examples.append(tokenized_text[i:i + block_size])

    def __len__(self):
        return len(self.examples)

    def __getitem__(self, idx):
        return torch.tensor(self.examples[idx])


def load_custom_dataset(tokenizer, file_path, validation_split=0.1):
    dataset = TextDataset(tokenizer, file_path)
    train_size = int((1 - validation_split) * len(dataset))
    val_size = len(dataset) - train_size
    train_dataset, val_dataset = torch.utils.data.random_split(dataset, [train_size, val_size])
    return train_dataset, val_dataset


def fine_tune_gpt(train_dataset, val_dataset, vocab_size):
    # 定义设备
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = GPT(vocab_size).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    train_loader = DataLoader(train_dataset, batch_size=4, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=4)
    for epoch in range(5):
        model.train()
        total_loss = 0
        for batch in train_loader:
            src = batch.to(device)
            target = torch.roll(batch, -1, dims=1)
            target[:, -1] = 0
            optimizer.zero_grad()
            output = model(src)
            loss = criterion(output.view(-1, vocab_size), target.view(-1))
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        print(f"Epoch {epoch + 1}/5, Train Loss: {total_loss / len(train_dataset)}")
        model.eval()
        total_loss = 0
        with torch.no_grad():
            for batch in val_loader:
                src = batch.to(device)
                target = torch.roll(batch, -1, dims=1)
                target[:, -1] = 0
                output = model(src)
                loss = criterion(output.view(-1, vocab_size), target.view(-1))
                total_loss += loss.item()
        print(f"Epoch {epoch + 1}/5, Validation Loss: {total_loss / len(val_loader)}")
    return model


def answer_question(model, tokenizer, question, max_length=150):
    input_ids = tokenizer.encode(question, return_tensors='pt').to(device)
    with torch.no_grad():
        output = model(input_ids)
        output = torch.argmax(output[:, -1, :], dim=-1)
        answer = [output.item()]
        for _ in range(max_length - 1):
            new_input = torch.tensor([answer]).to(device)
            new_output = model(new_input)
            new_token = torch.argmax(new_output[:, -1, :], dim=-1)
            answer.append(new_token.item())
    answer_text = tokenizer.decode(answer)
    return answer_text


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("debug.log"),
            logging.StreamHandler()
        ]
    )


def main():
    setup_logging()
    logging.info("Starting the GPT based QA system")
    tokenizer = GPT2Tokenizer.from_pretrained('gpt2')
    vocab_size = tokenizer.vocab_size
    train_dataset, val_dataset = load_custom_dataset(tokenizer, 'path_to_your_dataset.txt')
    # 定义设备
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    fine_tuned_model = fine_tune_gpt(train_dataset, val_dataset, vocab_size)
    while True:
        question = input("Ask a question (type 'exit' to quit): ")
        if question.lower() == 'exit':
            break
        answer = answer_question(fine_tuned_model, tokenizer, question)
        print(f"Answer: {answer}")


if __name__ == "__main__":
    main()