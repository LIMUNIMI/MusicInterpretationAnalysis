from time import time

import numpy as np
from tqdm import tqdm

import torch
import torch.nn.functional as F

from . import data_management, feature_extraction, plotting
from . import settings as s


def train_pedaling(nmf_params):
    validloader = data_management.get_loader(['validation'], nmf_params,
                                             'pedaling')
    trainloader = data_management.get_loader(['train'], nmf_params, 'pedaling')
    model = feature_extraction.MIDIParameterEstimation(s.BINS, 3).to(
        s.DEVICE).to(s.DTYPE)
    train(trainloader, validloader, model)


def train_velocity(nmf_params):
    validloader = data_management.get_loader(['validation'], nmf_params,
                                             'velocity')
    trainloader = data_management.get_loader(['train'], nmf_params, 'velocity')
    model = feature_extraction.MIDIVelocityEstimation(s.BINS).to(s.DEVICE).to(
        s.DTYPE)

    train(trainloader, validloader, model)


def train(trainloader, validloader, model):
    optim = torch.optim.Adadelta(model.parameters(), lr=s.LR_VELOCITY)

    def trainloss_fn(x, y, lens=None):
        y /= 127

        if not lens:
            return F.l1_loss(x, y)

        loss = torch.zeros(len(lens))
        for batch, L in enumerate(lens):
            loss[batch] = F.l1_loss(x[batch, :L], y[batch, :L])
        return loss

    validloss_fn = trainloss_fn
    train_epoch(model, optim, trainloss_fn, validloss_fn, trainloader,
                validloader)


def train_epoch(model, optim, trainloss_fn, validloss_fn, trainloader,
                validloader):
    """
    A typical training algorithm with early stopping and loss plotting
    """
    best_epoch = 0
    best_loss = 9999
    for epoch in range(s.EPOCHS):
        epoch_ttt = time()
        print(f"-- Epoch {epoch} --")
        trainloss, validloss, trainloss_valid = [], [], []
        print("-> Training")
        model.train()
        for inputs, targets, lens in tqdm(trainloader):
            inputs = inputs.to(s.DEVICE).to(s.DTYPE)
            targets = targets.to(s.DEVICE).to(s.DTYPE)

            optim.zero_grad()
            out = model(inputs)
            loss = trainloss_fn(out, targets, lens)
            loss.backward()
            optim.step()
            trainloss.append(loss.detach().cpu().numpy())

        trainloss = np.mean(trainloss)
        print(f"training loss : {trainloss:.4e}")

        print("-> Validating")
        with torch.no_grad():
            model.eval()
            for inputs, targets, lens in tqdm(validloader):
                inputs = inputs.to(s.DEVICE).to(s.DTYPE)
                targets = targets.to(s.DEVICE).to(s.DTYPE)
                # targets = torch.argmax(targets, dim=1).to(torch.float)

                out = model(inputs)
                validloss.append(
                    validloss_fn(targets, out, lens).detach().cpu().numpy())
                trainloss_valid.append(
                    trainloss_fn(targets, out, lens).detach().cpu().numpy())

        validloss = np.mean(validloss)
        trainloss_valid = np.mean(trainloss_valid)
        print(f"validation loss : {validloss:.4e}")
        print(f"validation-training loss : {validloss:.4e}")
        if validloss < best_loss:
            best_loss = validloss
            best_epoch = epoch
            state_dict = model.cpu().state_dict()
            name = f"checkpoints/checkpoint{best_loss:.4f}.pt"
            torch.save({'dtype': model.dtype, 'state_dict': state_dict}, name)
        elif epoch - best_epoch > s.EARLY_STOP:
            print("-- Early stop! --")
            break
        else:
            print(f"{epoch - best_epoch} from early stop!!")

        if s.PLOT_LOSSES:
            plotting.plot_losses(trainloss, validloss, trainloss_valid, epoch)

        print("Time for this epoch: ", time() - epoch_ttt)
