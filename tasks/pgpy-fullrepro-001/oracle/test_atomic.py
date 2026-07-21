""" test the functionality of PGPKeyring
"""
import pytest
import glob
import os
from pathlib import Path

from pgpy import PGPKey
from pgpy import PGPKeyring
from pgpy import PGPUID


DATA_DIR = Path(__file__).with_name("data")

@pytest.fixture
def abe_image():
    path = DATA_DIR / "abe.jpg"
    with path.open("rb") as abef:
        abebytes = bytearray(path.stat().st_size)
        abef.readinto(abebytes)
    return PGPUID.new(abebytes)

@pytest.fixture
def un():
    return PGPUID.new("Temperair\u00e9e Youx'seur")

@pytest.fixture
def unc():
    return PGPUID.new("Temperair\u00e9e Youx'seur", comment="\u2603")

@pytest.fixture
def une():
    return PGPUID.new("Temperair\u00e9e Youx'seur", email='snowman@not.an.email.addre.ss')

@pytest.fixture
def unce():
    return PGPUID.new("Temperair\u00e9e Youx'seur", comment="\u2603", email='snowman@not.an.email.addre.ss')

@pytest.fixture
def abe():
    return PGPUID.new('Abraham Lincoln', comment='Honest Abe', email='abraham.lincoln@whitehouse.gov')

class TestPGPUID(object):

    def test_userid(self, abe):
        assert abe.name == 'Abraham Lincoln'
        assert abe.comment == 'Honest Abe'
        assert abe.email == 'abraham.lincoln@whitehouse.gov'
        assert abe.image is None

    def test_userphoto(self, abe_image):
        assert abe_image.name == ''
        assert abe_image.comment == ''
        assert abe_image.email == ''
        path = DATA_DIR / "abe.jpg"
        with path.open("rb") as abef:
            abebytes = bytearray(path.stat().st_size)
            abef.readinto(abebytes)
        assert abe_image.image == abebytes

    def test_format(self, un, unc, une, unce):
        assert '{:s}'.format(un) == "Temperair\u00e9e Youx'seur"
        assert '{:s}'.format(unc) == "Temperair\u00e9e Youx'seur (\u2603)"
        assert '{:s}'.format(une) == "Temperair\u00e9e Youx'seur <snowman@not.an.email.addre.ss>"
        assert '{:s}'.format(unce) == "Temperair\u00e9e Youx'seur (\u2603) <snowman@not.an.email.addre.ss>"
_keyfiles = sorted(glob.glob(str(DATA_DIR / 'blocks/*key*.asc')))
_fingerprints = {'dsapubkey.asc': '2B5BBB143BA0B290DCEE6668B798AE8990877201', 'dsaseckey.asc': '2B5BBB143BA0B290DCEE6668B798AE8990877201', 'eccpubkey.asc': '502D1A5365D1C0CAA69945390BA52DF0BAA59D9C', 'eccseckey.asc': '502D1A5365D1C0CAA69945390BA52DF0BAA59D9C', 'openpgp.js.pubkey.asc': 'C7C38ECEE94A4AD32DDB064E14AB44C74D1BDAB8', 'openpgp.js.seckey.asc': 'C7C38ECEE94A4AD32DDB064E14AB44C74D1BDAB8', 'rsapubkey.asc': 'F4294BC8094A7E0585C85E8637473B3758C44F36', 'rsaseckey.asc': 'F4294BC8094A7E0585C85E8637473B3758C44F36'}

class TestPGPKey(object):

    @pytest.mark.parametrize('kf', _keyfiles, ids=[os.path.basename(f) for f in _keyfiles])
    def test_load_from_file(self, kf):
        (key, _) = PGPKey.from_file(kf)
        assert key.fingerprint == _fingerprints[os.path.basename(kf)]

    @pytest.mark.parametrize('kf', _keyfiles, ids=[os.path.basename(f) for f in _keyfiles])
    def test_load_from_str(self, kf):
        with open(kf, 'r') as tkf:
            (key, _) = PGPKey.from_blob(tkf.read())
        assert key.fingerprint == _fingerprints[os.path.basename(kf)]

    @pytest.mark.parametrize('kf', _keyfiles, ids=[os.path.basename(f) for f in _keyfiles])
    def test_load_from_bytes(self, kf):
        with open(kf, 'rb') as tkf:
            (key, _) = PGPKey.from_blob(tkf.read())
        assert key.fingerprint == _fingerprints[os.path.basename(kf)]

    @pytest.mark.parametrize('kf', _keyfiles, ids=[os.path.basename(f) for f in _keyfiles])
    def test_load_from_bytearray(self, kf):
        tkb = bytearray(os.stat(kf).st_size)
        with open(kf, 'rb') as tkf:
            tkf.readinto(tkb)
        (key, _) = PGPKey.from_blob(tkb)
        assert key.fingerprint == _fingerprints[os.path.basename(kf)]

    @pytest.mark.parametrize(
        'kf',
        sorted(filter(lambda f: not f.endswith('enc.asc'), glob.glob(str(DATA_DIR / 'keys/*.asc')))),
        ids=lambda value: os.path.basename(value),
    )
    def test_save(self, kf):
        (key, _) = PGPKey.from_file(kf)
        pgpyblob = key.__bytes__()
        (reloaded, _) = PGPKey.from_file(kf)
        assert pgpyblob == reloaded.__bytes__()

@pytest.fixture(scope='module')
def keyring():
    return PGPKeyring()

class TestPGPKeyring(object):

    @pytest.mark.parametrize('kf', _keyfiles, ids=[os.path.basename(f) for f in _keyfiles])
    def test_load_key_instance(self, keyring, kf):
        (key, _) = PGPKey.from_file(kf)
        keys = keyring.load(key)
        assert key.fingerprint in keyring
        for uid in key.userids:
            if uid.name != '':
                assert uid.name in keyring
            if uid.email != '':
                assert uid.email in keyring
        with keyring.key(key.fingerprint) as loaded_key:
            assert loaded_key.fingerprint == key.fingerprint
