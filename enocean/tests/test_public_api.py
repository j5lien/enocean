import enocean


def test_public_api_is_importable_from_the_package():
    for name in enocean.__all__:
        assert getattr(enocean, name) is not None, name


def test_version():
    assert enocean.__version__ and enocean.__version__[0].isdigit()


def test_same_objects_as_the_modules():
    from enocean.communicators.serialcommunicator import SerialCommunicator
    from enocean.protocol.packet import RadioPacket

    assert enocean.SerialCommunicator is SerialCommunicator
    assert enocean.RadioPacket is RadioPacket
