from ._feature_extractor import _FeatureExtractor
from .. import submodules, weight_init


class MobileNetV2(_FeatureExtractor):
    def __init__(self, feature_channels=1280):
        super().__init__(feature_channels)

        self.initial = submodules.conv(3, 32, stride=2)
        self.block1 = submodules.inverted_residuals(32, 16, expansion=1)
        self.block2 = submodules.inverted_residuals(16, 24, stride=2, blocks=2)
        self.block3 = submodules.inverted_residuals(24, 32, stride=2, blocks=3)
        self.block4a = submodules.inverted_residuals(32, 64, stride=2, blocks=4)
        self.block4b = submodules.inverted_residuals(64, 96, blocks=3)
        self.block5a = submodules.inverted_residuals(
            96, 160, stride=2, blocks=3
        )
        self.block5b = submodules.inverted_residuals(160, 320)
        self.final = submodules.conv(320, self.feature_channels, 1)

        weight_init.init(self.modules())

    def forward(self, input_):
        initial = self.initial(input_)
        block1 = self.block1(initial)
        block2 = self.block2(block1)
        block3 = self.block3(block2)
        block4a = self.block4a(block3)
        block4b = self.block4b(block4a)
        block5a = self.block5a(block4b)
        block5b = self.block5b(block5a)
        final = self.final(block5b)
        return final
