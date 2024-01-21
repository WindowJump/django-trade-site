class InsufficientCoinsError(Exception):
    def __init__(self, message='Not enough coins on balance'):
        self.message = f'{self.__class__.__name__}: {message}'
        super().__init__(self.message)


class InsufficientUSDTError(Exception):
    def __init__(self, message='Not enough USDT on balance'):
        self.message = f'{self.__class__.__name__}: {message}'
        super().__init__(self.message)


class WalletTypeError(Exception):
    def __init__(self, message='offer_usdt_wallet.coin_type can be only USDT'):
        self.message = f'{self.__class__.__name__}: {message}'
        super().__init__(self.message)
