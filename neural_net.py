"""
/*
 * Copyright (c) 2026 Jérôme Welscher
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 */
 """


import torch
import torch.optim
import numpy as np
from torch.utils.data import DataLoader, TensorDataset
from sklearn.model_selection import train_test_split


X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=11)
X_train_t, X_test_t, y_train_t, y_test_t = train_test_split(X, y_t, test_size=0.2, random_state=11)

train_dataset = TensorDataset(
    torch.tensor(X_train, dtype=torch.float32), 
    torch.tensor(np.log1p(y_train), dtype=torch.float32)
)
val_dataset = TensorDataset(
    torch.tensor(X_test, dtype=torch.float32), 
    torch.tensor(np.log1p(y_test), dtype=torch.float32)
)

training_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
validation_loader = DataLoader(val_dataset, batch_size=32, shuffle=False)

train_dataset_t = TensorDataset(
    torch.tensor(X_train_t, dtype=torch.float32), 
    torch.tensor(np.log1p(y_train_t), dtype=torch.float32)
)
val_dataset_t = TensorDataset(
    torch.tensor(X_test_t, dtype=torch.float32), 
    torch.tensor(np.log1p(y_test_t), dtype=torch.float32)
)

training_loader_t = DataLoader(train_dataset_t, batch_size=32, shuffle=True)
validation_loader_t = DataLoader(val_dataset_t, batch_size=32, shuffle=False)

class MeanStdModel(torch.nn.Module):
    def __init__(self):
        super(MeanStdModel, self).__init__()

        self.linear1 = torch.nn.Linear(1, 48)
        self.linear2 = torch.nn.Linear(48, 16)
        self.activation = torch.nn.LeakyReLU()
        self.linear3 = torch.nn.Linear(16, 2)
        self.softplus = torch.nn.Softplus()

    def forward(self, x):
        x = self.linear1(x)
        x = self.activation(x)
        x = self.linear2(x)
        x = self.activation(x)
        x = self.linear3(x)
        
        mean = x[:, 0]
        std = self.softplus(x[:, 1])
        
        return mean, std


def train_one_epoch(epoch_index, train_load, model, optimizer, loss_fn):
    running_loss = 0.
    last_loss = 0.
        
    for i, data in enumerate(train_load):
        inputs, labels = data
        
        optimizer.zero_grad()

        mean, std = model(inputs.unsqueeze(1))

        var = std**2

        mean = mean.unsqueeze(1)
        var = var.unsqueeze(1)

        loss = loss_fn(mean, labels.unsqueeze(1), var)
        loss.backward()

        optimizer.step()

        running_loss += loss.item()
        if i % 100 == 99:
            last_loss = running_loss / 100 # loss per batch            running_loss = 0.

    return last_loss

def train(epoch_num, train_load, val_load, model, optimizer, loss_fn, name):
    epoch_number = 0
    best_vloss = 1000000
    for epoch in range(epoch_num):
        model.train(True)
        avg_loss = train_one_epoch(epoch_number, train_load, model, optimizer, loss_fn)
        
        running_vloss = 0.0
        model.eval()
    
        with torch.no_grad():
            for i, vdata in enumerate(val_load):
                vinputs, vlabels = vdata
                vmean, vstd = model(vinputs.unsqueeze(1))
                vvar = vstd**2
    
                vmean = vmean.unsqueeze(1)
                vvar = vvar.unsqueeze(1)
                
                vloss = loss_fn(vmean, vlabels.unsqueeze(1), vvar)
                running_vloss += vloss
                
        avg_vloss = running_vloss / (i + 1)
        if epoch % 25 == 0:
            print('EPOCH {}:'.format(epoch_number + 1))
            print('LOSS train {} valid {}'.format(avg_loss, avg_vloss))
    
        if avg_vloss < best_vloss:
            best_vloss = avg_vloss
            model_path = 'model_{}'.format(name)
            torch.save(neural_model.state_dict(), model_path)
    
        epoch_number += 1

EPOCHS = 201

neural_model = MeanStdModel()
neural_model_t = MeanStdModel()
loss_fn = torch.nn.GaussianNLLLoss(full=True)
loss_fn_t = torch.nn.GaussianNLLLoss(full=True)
optimizer = torch.optim.Adam(neural_model.parameters(), lr=0.0001)
optimizer_t = torch.optim.Adam(neural_model_t.parameters(), lr=0.0001)


train(EPOCHS, training_loader, validation_loader, neural_model, optimizer, loss_fn, "step_model")
train(EPOCHS, training_loader_t, validation_loader_t, neural_model_t, optimizer_t, loss_fn_t, "time_model")