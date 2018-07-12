from beauty import networks, metrics, lr_schedulers, data_loaders
from beauty.model_runners import Trainer, Evaluator
from beauty.utils import tensor_utils, serialization


class ModelTrainer:
    def __init__(self, config, resume_from=None):
        self.config = config
        self.start_epoch = 0
        self.device = tensor_utils.get_device()

        self.train_loader = data_loaders.create_data_loader(
            config.input.train, 'train'
        )
        self.val_loader = data_loaders.create_data_loader(
            config.input.val, 'val', pin_memory=False
        )
        self.model = networks.create_model(config.model, self.device)
        self.loss = config.model.loss()
        self.metrics = metrics.create_metric_bundle(config.metrics)
        self.optimizer = config.optimizer.optimizer(
            self.model.parameters(), **vars(config.optimizer.config)
        )
        self.best_meters = self.metrics.create_max_meters()

        self.trainer = Trainer(
            self.model, self.loss, self.metrics, config.input.train
        )
        self.evaluator = Evaluator(
            self.model, self.loss, self.metrics, config.input.val
        )
        self.scheduler = lr_schedulers.create_lr_scheduler(
            config.lr, self.optimizer
        )

    def train(self):
        for epoch in range(self.start_epoch, self.config.training.epochs):
            self.trainer.run(
                self.train_loader, epoch,
                optimizer=self.optimizer, scheduler=self.scheduler
            )
            metric_meters = self.evaluator.run(self.val_loader, epoch)
            self.log_training(epoch, metric_meters, self.config.log_dir)

    def resume(self, checkpoint_path, refresh=True):
        checkpoint = serialization.load_checkpoint(checkpoint_path)
        self.model.load_state_dict(checkpoint['state_dict'])
        if not refresh:
            self.start_epoch = checkpoint['epoch']
            self.optimizer.load_state_dict(checkpoint['optimizer'])
        print('Training resumed')
        print('Start epoch: {:3d}'.format(self.start_epoch))
        print('Best metrics: {}'.format(checkpoint['best_meters']))

    def log_training(self, epoch, metric_meters, log_dir):
        are_best = {}
        print('\n * Finished epoch {:3d}:\t'.format(epoch), end='')

        self.best_meters.update(metric_meters)
        print(self.best_meters)
        print()
        print()

        checkpoint = {
            'epoch': epoch + 1,
            'state_dict': self.model.state_dict(),
            'optimizer': self.optimizer.state_dict(),
            'best_meters': self.best_meters
        }
        serialization.save_checkpoint(checkpoint, are_best, log_dir=log_dir)
