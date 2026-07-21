# Spec2Repo oracle - integration tests for authlib-fullrepro-001
# Source: selected tests from filter/rewritten_upstream_tests.py

import base64

import copy

import datetime

import json

import os

import pytest

from cryptography.exceptions import InvalidTag

from cryptography.hazmat.primitives.keywrap import InvalidUnwrap

from authlib.jose import ECKey

from authlib.jose import JsonWebEncryption

from authlib.jose import JsonWebKey

from authlib.jose import JsonWebSignature

from authlib.jose import JsonWebToken

from authlib.jose import JWTClaims

from authlib.jose import KeySet

from authlib.jose import OctKey

from authlib.jose import OKPKey

from authlib.jose import RSAKey

from authlib.jose import errors

from authlib.jose import jwt

from authlib.jose.errors import DecodeError

from authlib.jose.errors import InvalidAlgorithmForMultipleRecipientsMode

from authlib.jose.errors import InvalidHeaderParameterNameError

from authlib.jose.errors import UnsupportedAlgorithmError

TEST_FILES = {'ed25519-pkcs8.pem': '-----BEGIN PRIVATE KEY-----\nMC4CAQAwBQYDK2VwBCIEIJ1hsZ3v/VpguoRK9JLsLMREScVpezJpGXA7rAMcrn9g\n-----END PRIVATE KEY-----\n', 'ed25519-pub.pem': '-----BEGIN PUBLIC KEY-----\nMCowBQYDK2VwAyEA11qYAYKxCrfVS/7TyWQHOg7hcvPapiMlrwIaaPcHURo=\n-----END PUBLIC KEY-----\n', 'ed25519-ssh.pub': 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIAA/RNCWJ6VfjsWW3fGjdbeM+9VbX+iXCQu02B09Bw24 demo@authlib.org\n', 'jwk_private.json': {'kty': 'RSA', 'kid': 'bilbo.baggins@hobbiton.example', 'use': 'sig', 'n': 'n4EPtAOCc9AlkeQHPzHStgAbgs7bTZLwUBZdR8_KuKPEHLd4rHVTeT-O-XV2jRojdNhxJWTDvNd7nqQ0VEiZQHz_AJmSCpMaJMRBSFKrKb2wqVwGU_NsYOYL-QtiWN2lbzcEe6XC0dApr5ydQLrHqkHHig3RBordaZ6Aj-oBHqFEHYpPe7Tpe-OfVfHd1E6cS6M1FZcD1NNLYD5lFHpPI9bTwJlsde3uhGqC0ZCuEHg8lhzwOHrtIQbS0FVbb9k3-tVTU4fg_3L_vniUFAKwuCLqKnS2BYwdq_mzSnbLY7h_qixoR7jig3__kRhuaxwUkRz5iaiQkqgc5gHdrNP5zw', 'e': 'AQAB', 'd': 'bWUC9B-EFRIo8kpGfh0ZuyGPvMNKvYWNtB_ikiH9k20eT-O1q_I78eiZkpXxXQ0UTEs2LsNRS-8uJbvQ-A1irkwMSMkK1J3XTGgdrhCku9gRldY7sNA_AKZGh-Q661_42rINLRCe8W-nZ34ui_qOfkLnK9QWDDqpaIsA-bMwWWSDFu2MUBYwkHTMEzLYGqOe04noqeq1hExBTHBOBdkMXiuFhUq1BU6l-DqEiWxqg82sXt2h-LMnT3046AOYJoRioz75tSUQfGCshWTBnP5uDjd18kKhyv07lhfSJdrPdM5Plyl21hsFf4L_mHCuoFau7gdsPfHPxxjVOcOpBrQzwQ', 'p': '3Slxg_DwTXJcb6095RoXygQCAZ5RnAvZlno1yhHtnUex_fp7AZ_9nRaO7HX_-SFfGQeutao2TDjDAWU4Vupk8rw9JR0AzZ0N2fvuIAmr_WCsmGpeNqQnev1T7IyEsnh8UMt-n5CafhkikzhEsrmndH6LxOrvRJlsPp6Zv8bUq0k', 'q': 'uKE2dh-cTf6ERF4k4e_jy78GfPYUIaUyoSSJuBzp3Cubk3OCqs6grT8bR_cu0Dm1MZwWmtdqDyI95HrUeq3MP15vMMON8lHTeZu2lmKvwqW7anV5UzhM1iZ7z4yMkuUwFWoBvyY898EXvRD-hdqRxHlSqAZ192zB3pVFJ0s7pFc', 'dp': 'B8PVvXkvJrj2L-GYQ7v3y9r6Kw5g9SahXBwsWUzp19TVlgI-YV85q1NIb1rxQtD-IsXXR3-TanevuRPRt5OBOdiMGQp8pbt26gljYfKU_E9xn-RULHz0-ed9E9gXLKD4VGngpz-PfQ_q29pk5xWHoJp009Qf1HvChixRX59ehik', 'dq': 'CLDmDGduhylc9o7r84rEUVn7pzQ6PF83Y-iBZx5NT-TpnOZKF1pErAMVeKzFEl41DlHHqqBLSM0W1sOFbwTxYWZDm6sI6og5iTbwQGIC3gnJKbi_7k_vJgGHwHxgPaX2PnvP-zyEkDERuf-ry4c_Z11Cq9AqC2yeL6kdKT1cYF8', 'qi': '3PiqvXQN0zwMeE-sBvZgi289XP9XCQF3VWqPzMKnIgQp7_Tugo6-NZBKCQsMf3HaEGBjTVJs_jcK8-TRXvaKe-7ZMaQj8VfBdYkssbu0NKDDhjJ-GtiseaDVWt7dcH0cfwxgFUHpQh7FoCrjFJ6h6ZEpMF6xmujs4qMpPz8aaI4'}, 'jwk_public.json': {'kty': 'RSA', 'kid': 'bilbo.baggins@hobbiton.example', 'use': 'sig', 'n': 'n4EPtAOCc9AlkeQHPzHStgAbgs7bTZLwUBZdR8_KuKPEHLd4rHVTeT-O-XV2jRojdNhxJWTDvNd7nqQ0VEiZQHz_AJmSCpMaJMRBSFKrKb2wqVwGU_NsYOYL-QtiWN2lbzcEe6XC0dApr5ydQLrHqkHHig3RBordaZ6Aj-oBHqFEHYpPe7Tpe-OfVfHd1E6cS6M1FZcD1NNLYD5lFHpPI9bTwJlsde3uhGqC0ZCuEHg8lhzwOHrtIQbS0FVbb9k3-tVTU4fg_3L_vniUFAKwuCLqKnS2BYwdq_mzSnbLY7h_qixoR7jig3__kRhuaxwUkRz5iaiQkqgc5gHdrNP5zw', 'e': 'AQAB'}, 'jwks_private.json': {'keys': [{'kty': 'RSA', 'kid': 'abc', 'n': 'pF1JaMSN8TEsh4N4O_5SpEAVLivJyLH-Cgl3OQBPGgJkt8cg49oasl-5iJS-VdrILxWM9_JCJyURpUuslX4Eb4eUBtQ0x5BaPa8-S2NLdGTaL7nBOO8o8n0C5FEUU-qlEip79KE8aqOj-OC44VsIquSmOvWIQD26n3fCVlgwoRBD1gzzsDOeaSyzpKrZR851Kh6rEmF2qjJ8jt6EkxMsRNACmBomzgA4M1TTsisSUO87444pe35Z4_n5c735o2fZMrGgMwiJNh7rT8SYxtIkxngioiGnwkxGQxQ4NzPAHg-XSY0J04pNm7KqTkgtxyrqOANJLIjXlR-U9SQ90NjHVQ', 'e': 'AQAB', 'd': 'G4E84ppZwm3fLMI0YZ26iJ_sq3BKcRpQD6_r0o8ZrZmO7y4Uc-ywoP7h1lhFzaox66cokuloZpKOdGHIfK-84EkI3WeveWHPqBjmTMlN_ClQVcI48mUbLhD7Zeenhi9y9ipD2fkNWi8OJny8k4GfXrGqm50w8schrsPksnxJjvocGMT6KZNfDURKF2HlM5X1uY8VCofokXOjBEeHIfYM8e7IcmPpyXwXKonDmVVbMbefo-u-TttgeyOYaO6s3flSy6Y0CnpWi43JQ_VEARxQl6Brj1oizr8UnQQ0nNCOWwDNVtOV4eSl7PZoiiT7CxYkYnhJXECMAM5YBpm4Qk9zdQ', 'p': '1g4ZGrXOuo75p9_MRIepXGpBWxip4V7B9XmO9WzPCv8nMorJntWBmsYV1I01aITxadHatO4Gl2xLniNkDyrEQzJ7w38RQgsVK-CqbnC0K9N77QPbHeC1YQd9RCNyUohOimKvb7jyv798FBU1GO5QI2eNgfnnfteSVXhD2iOoTOs', 'q': 'xJJ-8toxJdnLa0uUsAbql6zeNXGbUBMzu3FomKlyuWuq841jS2kIalaO_TRj5hbnE45jmCjeLgTVO6Ach3Wfk4zrqajqfFJ0zUg_Wexp49lC3RWiV4icBb85Q6bzeJD9Dn9vhjpfWVkczf_NeA1fGH_pcgfkT6Dm706GFFttLL8', 'dp': 'Zfx3l5NR-O8QIhzuHSSp279Afl_E6P0V2phdNa_vAaVKDrmzkHrXcl-4nPnenXrh7vIuiw_xkgnmCWWBUfylYALYlu-e0GGpZ6t2aIJIRa1QmT_CEX0zzhQcae-dk5cgHK0iO0_aUOOyAXuNPeClzAiVknz4ACZDsXdIlNFyaZs', 'dq': 'Z9DG4xOBKXBhEoWUPXMpqnlN0gPx9tRtWe2HRDkZsfu_CWn-qvEJ1L9qPSfSKs6ls5pb1xyeWseKpjblWlUwtgiS3cOsM4SI03H4o1FMi11PBtxKJNitLgvT_nrJ0z8fpux-xfFGMjXyFImoxmKpepLzg5nPZo6f6HscLNwsSJk', 'qi': 'Sk20wFvilpRKHq79xxFWiDUPHi0x0pp82dYIEntGQkKUWkbSlhgf3MAi5NEQTDmXdnB-rVeWIvEi-BXfdnNgdn8eC4zSdtF4sIAhYr5VWZo0WVWDhT7u2ccvZBFymiz8lo3gN57wGUCi9pbZqzV1-ZppX6YTNDdDCE0q-KO3Cec'}, {'kty': 'RSA', 'kid': 'bilbo.baggins@hobbiton.example', 'use': 'sig', 'n': 'n4EPtAOCc9AlkeQHPzHStgAbgs7bTZLwUBZdR8_KuKPEHLd4rHVTeT-O-XV2jRojdNhxJWTDvNd7nqQ0VEiZQHz_AJmSCpMaJMRBSFKrKb2wqVwGU_NsYOYL-QtiWN2lbzcEe6XC0dApr5ydQLrHqkHHig3RBordaZ6Aj-oBHqFEHYpPe7Tpe-OfVfHd1E6cS6M1FZcD1NNLYD5lFHpPI9bTwJlsde3uhGqC0ZCuEHg8lhzwOHrtIQbS0FVbb9k3-tVTU4fg_3L_vniUFAKwuCLqKnS2BYwdq_mzSnbLY7h_qixoR7jig3__kRhuaxwUkRz5iaiQkqgc5gHdrNP5zw', 'e': 'AQAB', 'd': 'bWUC9B-EFRIo8kpGfh0ZuyGPvMNKvYWNtB_ikiH9k20eT-O1q_I78eiZkpXxXQ0UTEs2LsNRS-8uJbvQ-A1irkwMSMkK1J3XTGgdrhCku9gRldY7sNA_AKZGh-Q661_42rINLRCe8W-nZ34ui_qOfkLnK9QWDDqpaIsA-bMwWWSDFu2MUBYwkHTMEzLYGqOe04noqeq1hExBTHBOBdkMXiuFhUq1BU6l-DqEiWxqg82sXt2h-LMnT3046AOYJoRioz75tSUQfGCshWTBnP5uDjd18kKhyv07lhfSJdrPdM5Plyl21hsFf4L_mHCuoFau7gdsPfHPxxjVOcOpBrQzwQ', 'p': '3Slxg_DwTXJcb6095RoXygQCAZ5RnAvZlno1yhHtnUex_fp7AZ_9nRaO7HX_-SFfGQeutao2TDjDAWU4Vupk8rw9JR0AzZ0N2fvuIAmr_WCsmGpeNqQnev1T7IyEsnh8UMt-n5CafhkikzhEsrmndH6LxOrvRJlsPp6Zv8bUq0k', 'q': 'uKE2dh-cTf6ERF4k4e_jy78GfPYUIaUyoSSJuBzp3Cubk3OCqs6grT8bR_cu0Dm1MZwWmtdqDyI95HrUeq3MP15vMMON8lHTeZu2lmKvwqW7anV5UzhM1iZ7z4yMkuUwFWoBvyY898EXvRD-hdqRxHlSqAZ192zB3pVFJ0s7pFc', 'dp': 'B8PVvXkvJrj2L-GYQ7v3y9r6Kw5g9SahXBwsWUzp19TVlgI-YV85q1NIb1rxQtD-IsXXR3-TanevuRPRt5OBOdiMGQp8pbt26gljYfKU_E9xn-RULHz0-ed9E9gXLKD4VGngpz-PfQ_q29pk5xWHoJp009Qf1HvChixRX59ehik', 'dq': 'CLDmDGduhylc9o7r84rEUVn7pzQ6PF83Y-iBZx5NT-TpnOZKF1pErAMVeKzFEl41DlHHqqBLSM0W1sOFbwTxYWZDm6sI6og5iTbwQGIC3gnJKbi_7k_vJgGHwHxgPaX2PnvP-zyEkDERuf-ry4c_Z11Cq9AqC2yeL6kdKT1cYF8', 'qi': '3PiqvXQN0zwMeE-sBvZgi289XP9XCQF3VWqPzMKnIgQp7_Tugo6-NZBKCQsMf3HaEGBjTVJs_jcK8-TRXvaKe-7ZMaQj8VfBdYkssbu0NKDDhjJ-GtiseaDVWt7dcH0cfwxgFUHpQh7FoCrjFJ6h6ZEpMF6xmujs4qMpPz8aaI4'}]}, 'jwks_public.json': {'keys': [{'kty': 'RSA', 'kid': 'abc', 'n': 'pF1JaMSN8TEsh4N4O_5SpEAVLivJyLH-Cgl3OQBPGgJkt8cg49oasl-5iJS-VdrILxWM9_JCJyURpUuslX4Eb4eUBtQ0x5BaPa8-S2NLdGTaL7nBOO8o8n0C5FEUU-qlEip79KE8aqOj-OC44VsIquSmOvWIQD26n3fCVlgwoRBD1gzzsDOeaSyzpKrZR851Kh6rEmF2qjJ8jt6EkxMsRNACmBomzgA4M1TTsisSUO87444pe35Z4_n5c735o2fZMrGgMwiJNh7rT8SYxtIkxngioiGnwkxGQxQ4NzPAHg-XSY0J04pNm7KqTkgtxyrqOANJLIjXlR-U9SQ90NjHVQ', 'e': 'AQAB'}, {'kty': 'RSA', 'kid': 'bilbo.baggins@hobbiton.example', 'use': 'sig', 'n': 'n4EPtAOCc9AlkeQHPzHStgAbgs7bTZLwUBZdR8_KuKPEHLd4rHVTeT-O-XV2jRojdNhxJWTDvNd7nqQ0VEiZQHz_AJmSCpMaJMRBSFKrKb2wqVwGU_NsYOYL-QtiWN2lbzcEe6XC0dApr5ydQLrHqkHHig3RBordaZ6Aj-oBHqFEHYpPe7Tpe-OfVfHd1E6cS6M1FZcD1NNLYD5lFHpPI9bTwJlsde3uhGqC0ZCuEHg8lhzwOHrtIQbS0FVbb9k3-tVTU4fg_3L_vniUFAKwuCLqKnS2BYwdq_mzSnbLY7h_qixoR7jig3__kRhuaxwUkRz5iaiQkqgc5gHdrNP5zw', 'e': 'AQAB'}]}, 'jwks_single_private.json': {'keys': [{'kty': 'RSA', 'n': 'pF1JaMSN8TEsh4N4O_5SpEAVLivJyLH-Cgl3OQBPGgJkt8cg49oasl-5iJS-VdrILxWM9_JCJyURpUuslX4Eb4eUBtQ0x5BaPa8-S2NLdGTaL7nBOO8o8n0C5FEUU-qlEip79KE8aqOj-OC44VsIquSmOvWIQD26n3fCVlgwoRBD1gzzsDOeaSyzpKrZR851Kh6rEmF2qjJ8jt6EkxMsRNACmBomzgA4M1TTsisSUO87444pe35Z4_n5c735o2fZMrGgMwiJNh7rT8SYxtIkxngioiGnwkxGQxQ4NzPAHg-XSY0J04pNm7KqTkgtxyrqOANJLIjXlR-U9SQ90NjHVQ', 'e': 'AQAB', 'd': 'G4E84ppZwm3fLMI0YZ26iJ_sq3BKcRpQD6_r0o8ZrZmO7y4Uc-ywoP7h1lhFzaox66cokuloZpKOdGHIfK-84EkI3WeveWHPqBjmTMlN_ClQVcI48mUbLhD7Zeenhi9y9ipD2fkNWi8OJny8k4GfXrGqm50w8schrsPksnxJjvocGMT6KZNfDURKF2HlM5X1uY8VCofokXOjBEeHIfYM8e7IcmPpyXwXKonDmVVbMbefo-u-TttgeyOYaO6s3flSy6Y0CnpWi43JQ_VEARxQl6Brj1oizr8UnQQ0nNCOWwDNVtOV4eSl7PZoiiT7CxYkYnhJXECMAM5YBpm4Qk9zdQ', 'p': '1g4ZGrXOuo75p9_MRIepXGpBWxip4V7B9XmO9WzPCv8nMorJntWBmsYV1I01aITxadHatO4Gl2xLniNkDyrEQzJ7w38RQgsVK-CqbnC0K9N77QPbHeC1YQd9RCNyUohOimKvb7jyv798FBU1GO5QI2eNgfnnfteSVXhD2iOoTOs', 'q': 'xJJ-8toxJdnLa0uUsAbql6zeNXGbUBMzu3FomKlyuWuq841jS2kIalaO_TRj5hbnE45jmCjeLgTVO6Ach3Wfk4zrqajqfFJ0zUg_Wexp49lC3RWiV4icBb85Q6bzeJD9Dn9vhjpfWVkczf_NeA1fGH_pcgfkT6Dm706GFFttLL8', 'dp': 'Zfx3l5NR-O8QIhzuHSSp279Afl_E6P0V2phdNa_vAaVKDrmzkHrXcl-4nPnenXrh7vIuiw_xkgnmCWWBUfylYALYlu-e0GGpZ6t2aIJIRa1QmT_CEX0zzhQcae-dk5cgHK0iO0_aUOOyAXuNPeClzAiVknz4ACZDsXdIlNFyaZs', 'dq': 'Z9DG4xOBKXBhEoWUPXMpqnlN0gPx9tRtWe2HRDkZsfu_CWn-qvEJ1L9qPSfSKs6ls5pb1xyeWseKpjblWlUwtgiS3cOsM4SI03H4o1FMi11PBtxKJNitLgvT_nrJ0z8fpux-xfFGMjXyFImoxmKpepLzg5nPZo6f6HscLNwsSJk', 'qi': 'Sk20wFvilpRKHq79xxFWiDUPHi0x0pp82dYIEntGQkKUWkbSlhgf3MAi5NEQTDmXdnB-rVeWIvEi-BXfdnNgdn8eC4zSdtF4sIAhYr5VWZo0WVWDhT7u2ccvZBFymiz8lo3gN57wGUCi9pbZqzV1-ZppX6YTNDdDCE0q-KO3Cec'}]}, 'jwks_single_public.json': {'keys': [{'kty': 'RSA', 'kid': 'abc', 'n': 'pF1JaMSN8TEsh4N4O_5SpEAVLivJyLH-Cgl3OQBPGgJkt8cg49oasl-5iJS-VdrILxWM9_JCJyURpUuslX4Eb4eUBtQ0x5BaPa8-S2NLdGTaL7nBOO8o8n0C5FEUU-qlEip79KE8aqOj-OC44VsIquSmOvWIQD26n3fCVlgwoRBD1gzzsDOeaSyzpKrZR851Kh6rEmF2qjJ8jt6EkxMsRNACmBomzgA4M1TTsisSUO87444pe35Z4_n5c735o2fZMrGgMwiJNh7rT8SYxtIkxngioiGnwkxGQxQ4NzPAHg-XSY0J04pNm7KqTkgtxyrqOANJLIjXlR-U9SQ90NjHVQ', 'e': 'AQAB'}]}, 'rsa_private.pem': '-----BEGIN RSA PRIVATE KEY-----\nMIIEogIBAAKCAQEApF1JaMSN8TEsh4N4O/5SpEAVLivJyLH+Cgl3OQBPGgJkt8cg\n49oasl+5iJS+VdrILxWM9/JCJyURpUuslX4Eb4eUBtQ0x5BaPa8+S2NLdGTaL7nB\nOO8o8n0C5FEUU+qlEip79KE8aqOj+OC44VsIquSmOvWIQD26n3fCVlgwoRBD1gzz\nsDOeaSyzpKrZR851Kh6rEmF2qjJ8jt6EkxMsRNACmBomzgA4M1TTsisSUO87444p\ne35Z4/n5c735o2fZMrGgMwiJNh7rT8SYxtIkxngioiGnwkxGQxQ4NzPAHg+XSY0J\n04pNm7KqTkgtxyrqOANJLIjXlR+U9SQ90NjHVQIDAQABAoIBABuBPOKaWcJt3yzC\nNGGduoif7KtwSnEaUA+v69KPGa2Zju8uFHPssKD+4dZYRc2qMeunKJLpaGaSjnRh\nyHyvvOBJCN1nr3lhz6gY5kzJTfwpUFXCOPJlGy4Q+2Xnp4YvcvYqQ9n5DVovDiZ8\nvJOBn16xqpudMPLHIa7D5LJ8SY76HBjE+imTXw1EShdh5TOV9bmPFQqH6JFzowRH\nhyH2DPHuyHJj6cl8FyqJw5lVWzG3n6Prvk7bYHsjmGjurN35UsumNAp6VouNyUP1\nRAEcUJega49aIs6/FJ0ENJzQjlsAzVbTleHkpez2aIok+wsWJGJ4SVxAjADOWAaZ\nuEJPc3UCgYEA1g4ZGrXOuo75p9/MRIepXGpBWxip4V7B9XmO9WzPCv8nMorJntWB\nmsYV1I01aITxadHatO4Gl2xLniNkDyrEQzJ7w38RQgsVK+CqbnC0K9N77QPbHeC1\nYQd9RCNyUohOimKvb7jyv798FBU1GO5QI2eNgfnnfteSVXhD2iOoTOsCgYEAxJJ+\n8toxJdnLa0uUsAbql6zeNXGbUBMzu3FomKlyuWuq841jS2kIalaO/TRj5hbnE45j\nmCjeLgTVO6Ach3Wfk4zrqajqfFJ0zUg/Wexp49lC3RWiV4icBb85Q6bzeJD9Dn9v\nhjpfWVkczf/NeA1fGH/pcgfkT6Dm706GFFttLL8CgYBl/HeXk1H47xAiHO4dJKnb\nv0B+X8To/RXamF01r+8BpUoOubOQetdyX7ic+d6deuHu8i6LD/GSCeYJZYFR/KVg\nAtiW757QYalnq3ZogkhFrVCZP8IRfTPOFBxp752TlyAcrSI7T9pQ47IBe4094KXM\nCJWSfPgAJkOxd0iU0XJpmwKBgGfQxuMTgSlwYRKFlD1zKap5TdID8fbUbVnth0Q5\nGbH7vwlp/qrxCdS/aj0n0irOpbOaW9ccnlrHiqY25VpVMLYIkt3DrDOEiNNx+KNR\nTItdTwbcSiTYrS4L0/56ydM/H6bsfsXxRjI18hSJqMZiqXqS84OZz2aOn+h7HCzc\nLEiZAoGASk20wFvilpRKHq79xxFWiDUPHi0x0pp82dYIEntGQkKUWkbSlhgf3MAi\n5NEQTDmXdnB+rVeWIvEi+BXfdnNgdn8eC4zSdtF4sIAhYr5VWZo0WVWDhT7u2ccv\nZBFymiz8lo3gN57wGUCi9pbZqzV1+ZppX6YTNDdDCE0q+KO3Cec=\n-----END RSA PRIVATE KEY-----\n', 'rsa_public.pem': '-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEApF1JaMSN8TEsh4N4O/5S\npEAVLivJyLH+Cgl3OQBPGgJkt8cg49oasl+5iJS+VdrILxWM9/JCJyURpUuslX4E\nb4eUBtQ0x5BaPa8+S2NLdGTaL7nBOO8o8n0C5FEUU+qlEip79KE8aqOj+OC44VsI\nquSmOvWIQD26n3fCVlgwoRBD1gzzsDOeaSyzpKrZR851Kh6rEmF2qjJ8jt6EkxMs\nRNACmBomzgA4M1TTsisSUO87444pe35Z4/n5c735o2fZMrGgMwiJNh7rT8SYxtIk\nxngioiGnwkxGQxQ4NzPAHg+XSY0J04pNm7KqTkgtxyrqOANJLIjXlR+U9SQ90NjH\nVQIDAQAB\n-----END PUBLIC KEY-----\n', 'secp256k1-private.pem': '-----BEGIN PRIVATE KEY-----\nMIGEAgEAMBAGByqGSM49AgEGBSuBBAAKBG0wawIBAQQgTHXBopHraQcg1U8bPK63\neO5tNMt5ZcHo/1RsJkSnLAahRANCAAROhceIcao7c/9Ei6PgBLr3+UgDbkxSCJ0d\nKDtXgKipXfrI1mVHys/FJ0TzvNPCEZNpPPeWYd/sr5V6ADhdQsHe\n-----END PRIVATE KEY-----\n', 'secp256k1-pub.pem': '-----BEGIN PUBLIC KEY-----\nMFYwEAYHKoZIzj0CAQYFK4EEAAoDQgAEToXHiHGqO3P/RIuj4AS69/lIA25MUgid\nHSg7V4CoqV36yNZlR8rPxSdE87zTwhGTaTz3lmHf7K+VegA4XULB3g==\n-----END PUBLIC KEY-----\n', 'secp521r1-private.json': {'kty': 'EC', 'kid': 'bilbo.baggins@hobbiton.example', 'use': 'sig', 'crv': 'P-521', 'x': 'AHKZLLOsCOzz5cY97ewNUajB957y-C-U88c3v13nmGZx6sYl_oJXu9A5RkTKqjqvjyekWF-7ytDyRXYgCF5cj0Kt', 'y': 'AdymlHvOiLxXkEhayXQnNCvDX4h9htZaCJN34kfmC6pV5OhQHiraVySsUdaQkAgDPrwQrJmbnX9cwlGfP-HqHZR1', 'd': 'AAhRON2r9cqXX1hg-RoI6R1tX5p2rUAYdmpHZoC1XNM56KtscrX6zbKipQrCW9CGZH3T4ubpnoTKLDYJ_fF3_rJt'}, 'secp521r1-public.json': {'kty': 'EC', 'kid': 'bilbo.baggins@hobbiton.example', 'use': 'sig', 'crv': 'P-521', 'x': 'AHKZLLOsCOzz5cY97ewNUajB957y-C-U88c3v13nmGZx6sYl_oJXu9A5RkTKqjqvjyekWF-7ytDyRXYgCF5cj0Kt', 'y': 'AdymlHvOiLxXkEhayXQnNCvDX4h9htZaCJN34kfmC6pV5OhQHiraVySsUdaQkAgDPrwQrJmbnX9cwlGfP-HqHZR1'}, 'ssh_private.pem': '-----BEGIN OPENSSH PRIVATE KEY-----\nb3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAABFwAAAAdzc2gtcn\nNhAAAAAwEAAQAAAQEApvV61Iw9YMrS8pAC9NAPf6ESkqNSpROGu+T0/hR7jSohlUpQk/C3\n65Zjlw+ivCY0WQeTrYMmqixx1UgSn4b6BDehsMAG72LugMO1edsXqhvhbXxEjZiogEHpkl\nA8u2O9fqaSaA2OcmQs+v7ptGAwYTxIPIM/5A4l8NKfwQy4qNrjPbFaDUQF8v6Y6/PgmoIm\nsT9eLKxcb2qZ0inBh7IdeeNoeJD25vql7qGrZrNizxf2QrmdvHLOk8a38jsVVnxf48/0pc\nH8jy+wMaeBEwlB1W68joFndKdSr+Nf8uYSCULeQRE3yTKPsNEJsODvtAWipWtA73UAc5fZ\nkTH69QXf7QAAA8jT7CeP0+wnjwAAAAdzc2gtcnNhAAABAQCm9XrUjD1gytLykAL00A9/oR\nKSo1KlE4a75PT+FHuNKiGVSlCT8LfrlmOXD6K8JjRZB5OtgyaqLHHVSBKfhvoEN6GwwAbv\nYu6Aw7V52xeqG+FtfESNmKiAQemSUDy7Y71+ppJoDY5yZCz6/um0YDBhPEg8gz/kDiXw0p\n/BDLio2uM9sVoNRAXy/pjr8+CagiaxP14srFxvapnSKcGHsh1542h4kPbm+qXuoatms2LP\nF/ZCuZ28cs6TxrfyOxVWfF/jz/SlwfyPL7Axp4ETCUHVbryOgWd0p1Kv41/y5hIJQt5BET\nfJMo+w0Qmw4O+0BaKla0DvdQBzl9mRMfr1Bd/tAAAAAwEAAQAAAQAHB1iXcBv5YjCFQ6jM\nM6IjZl2IzNVi27KVYGsr8yLMa5SkW0+PGtgzU853gpIAR792bAo8iMPs8BgOuY0HKECIQu\ntMrJjeJRUTWKngKmgRokDYQh4EtAOL+rphjX0xCl7k4RBSzxdLG4qFOowOKup+fXIxEflz\nmWDhhYxyLR3tBdCR64jm36oYuGZLv3UAH3p8CWrXW/EiWfHmiiEEtVsgVXZtX/QMKezJh0\n2BNBIGOa2bXV+I4sdrq/f49vLO0YiGaQ/Zx85fmzfoBMlQexqKWW/zbtxebf0sE9r5HAtv\nTb3LqXyb5Dqy1JI00Sm77QoZgiz524sRRwVTUyN0os9hAAAAgDEID/fmFnPcdHtX6Gnlkr\nfyivhrWUJGt1jmZLrXrCTB80XXJOF5yhym2p6Hwr3JDQKIIu6+eVUpnsMHeiU8WTBSKbnP\nBhtJFi/1uTLpJgTfLOZS7CewCkGqAIiUlVybz2GdIeyEKFwOkKwRSN7OqdanIoIX8zi7P8\nn/24xflap7AAAAgQDavsAywdgi96CdC7FIZK4X5nZuI7C7rrgPUkEb9KPnfNlT+N0QNIFK\nxyFfB0L3m2eGpJRKTtMGl1zKuD+Ecl729bnHqKKnbprd+jUlR8Bg9+Aq/rJtUue3nLBg08\n0bBUNewDmTp9R96uNr4ZiGYV6d3+ampgQ6+mukKKP6H8D6JQAAAIEAw2Tb6/c1+uKjwiYP\nHvnvpupXeFw7srnqp2eAxB3UmvhAqUB6tH0H+YADCFATbMB5nUPdnFW/q+wj0AE0R7Qcun\n7HvwztlZN9ZCYfvzy5hSZN3jdOk/I1TAObv6iDhuV0ZplP3kXZDPFT3VU7vcBBUkp04G5S\nWBgEKVBjECn1kCkAAAAQZGVtb0BhdXRobGliLm9yZwECAw==\n-----END OPENSSH PRIVATE KEY-----\n', 'ssh_public.pem': 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCm9XrUjD1gytLykAL00A9/oRKSo1KlE4a75PT+FHuNKiGVSlCT8LfrlmOXD6K8JjRZB5OtgyaqLHHVSBKfhvoEN6GwwAbvYu6Aw7V52xeqG+FtfESNmKiAQemSUDy7Y71+ppJoDY5yZCz6/um0YDBhPEg8gz/kDiXw0p/BDLio2uM9sVoNRAXy/pjr8+CagiaxP14srFxvapnSKcGHsh1542h4kPbm+qXuoatms2LPF/ZCuZ28cs6TxrfyOxVWfF/jz/SlwfyPL7Axp4ETCUHVbryOgWd0p1Kv41/y5hIJQt5BETfJMo+w0Qmw4O+0BaKla0DvdQBzl9mRMfr1Bd/t demo@authlib.org\n', 'thumbprint_example.json': {'kty': 'RSA', 'n': '0vx7agoebGcQSuuPiLJXZptN9nndrQmbXEps2aiAFbWhM78LhWx4cbbfAAtVT86zwu1RK7aPFFxuhDR1L6tSoc_BJECPebWKRXjBZCiFV4n3oknjhMstn64tZ_2W-5JsGY4Hc5n9yBXArwl93lqt7_RN5w6Cf0h4QyQ5v-65YGjQR0_FDW2QvzqY368QQMicAtaSqzs8KJZgnYb9c7d0zgdAZHzu6qMQvRL5hajrn1n91CbOpbISD08qNLyrdkt-bFTWhAI4vMQFh6WeZu0fM4lFd2NcRwr3XPksINHaQ-G_xBniIqbw0Ls1jF44-csFCur-kEgU8awapJzKnqDKgw', 'e': 'AQAB', 'alg': 'RS256', 'kid': '2011-04-29'}}

def read_file_path(name):
    value = TEST_FILES[name]
    return copy.deepcopy(value) if isinstance(value, (dict, list)) else value

def base64_to_int(value):
    raw = value.encode("ascii") if isinstance(value, str) else value
    raw += b"=" * (-len(raw) % 4)
    return int.from_bytes(base64.urlsafe_b64decode(raw), "big")

def json_dumps(value):
    return json.dumps(value)

def test_compact_jws():
    jws = JsonWebSignature(algorithms=["HS256"])
    s = jws.serialize({"alg": "HS256"}, "hello", "secret")
    data = jws.deserialize(s, "secret")
    header, payload = data["header"], data["payload"]
    assert payload == b"hello"
    assert header["alg"] == "HS256"
    assert "signature" not in data

def test_compact_rsa():
    jwe = JsonWebEncryption()
    s = jwe.serialize_compact(
        {"alg": "RSA-OAEP", "enc": "A256GCM"},
        "hello",
        read_file_path("rsa_public.pem"),
    )
    data = jwe.deserialize_compact(s, read_file_path("rsa_private.pem"))
    header, payload = data["header"], data["payload"]
    assert payload == b"hello"
    assert header["alg"] == "RSA-OAEP"

def test_compact_rsa_pss():
    jws = JsonWebSignature()
    private_key = read_file_path("rsa_private.pem")
    public_key = read_file_path("rsa_public.pem")
    s = jws.serialize({"alg": "PS256"}, "hello", private_key)
    data = jws.deserialize(s, public_key)
    header, payload = data["header"], data["payload"]
    assert payload == b"hello"
    assert header["alg"] == "PS256"
    ssh_pub_key = read_file_path("ssh_public.pem")
    with pytest.raises(errors.BadSignatureError):
        jws.deserialize(s, ssh_pub_key)

def test_compact_none():
    jws = JsonWebSignature(algorithms=["none"])
    s = jws.serialize({"alg": "none"}, "hello", None)
    data = jws.deserialize(s, None)
    header, payload = data["header"], data["payload"]
    assert payload == b"hello"
    assert header["alg"] == "none"

def test_flattened_json_jws():
    jws = JsonWebSignature()
    protected = {"alg": "HS256"}
    header = {"protected": protected, "header": {"kid": "a"}}
    s = jws.serialize(header, "hello", "secret")
    assert isinstance(s, dict)

    data = jws.deserialize(s, "secret")
    header, payload = data["header"], data["payload"]
    assert payload == b"hello"
    assert header["alg"] == "HS256"
    assert "protected" not in data

def test_nested_json_jws():
    jws = JsonWebSignature()
    protected = {"alg": "HS256"}
    header = {"protected": protected, "header": {"kid": "a"}}
    s = jws.serialize([header], "hello", "secret")
    assert isinstance(s, dict)
    assert "signatures" in s

    data = jws.deserialize(s, "secret")
    header, payload = data["header"], data["payload"]
    assert payload == b"hello"
    assert header[0]["alg"] == "HS256"
    assert "signatures" not in data

    # test bad signature
    with pytest.raises(errors.BadSignatureError):
        jws.deserialize(s, "f")

def test_function_key():
    protected = {"alg": "HS256"}
    header = [
        {"protected": protected, "header": {"kid": "a"}},
        {"protected": protected, "header": {"kid": "b"}},
    ]

    def load_key(header, payload):
        assert payload == b"hello"
        kid = header.get("kid")
        if kid == "a":
            return "secret-a"
        return "secret-b"

    jws = JsonWebSignature()
    s = jws.serialize(header, b"hello", load_key)
    assert isinstance(s, dict)
    assert "signatures" in s

    data = jws.deserialize(json.dumps(s), load_key)
    header, payload = data["header"], data["payload"]
    assert payload == b"hello"
    assert header[0]["alg"] == "HS256"
    assert "signature" not in data

def test_serialize_json_empty_payload():
    jws = JsonWebSignature()
    protected = {"alg": "HS256"}
    header = {"protected": protected, "header": {"kid": "a"}}
    s = jws.serialize_json(header, b"", "secret")
    data = jws.deserialize_json(s, "secret")
    assert data["payload"] == b""

def test_init_algorithms():
    _jwt = JsonWebToken(["RS256"])
    with pytest.raises(UnsupportedAlgorithmError):
        _jwt.encode({"alg": "HS256"}, {}, "k")

    _jwt = JsonWebToken("RS256")
    with pytest.raises(UnsupportedAlgorithmError):
        _jwt.encode({"alg": "HS256"}, {}, "k")

def test_encode_sensitive_data():
    # check=False won't raise error
    jwt.encode({"alg": "HS256"}, {"password": ""}, "k", check=False)
    with pytest.raises(errors.InsecureClaimError):
        jwt.encode(
            {"alg": "HS256"},
            {"password": ""},
            "k",
        )
    with pytest.raises(errors.InsecureClaimError):
        jwt.encode(
            {"alg": "HS256"},
            {"text": "4242424242424242"},
            "k",
        )

def test_encode_datetime():
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    id_token = jwt.encode({"alg": "HS256"}, {"exp": now}, "k")
    claims = jwt.decode(id_token, "k")
    assert isinstance(claims.exp, int)

def test_use_jws():
    payload = {"name": "hi"}
    private_key = read_file_path("rsa_private.pem")
    pub_key = read_file_path("rsa_public.pem")
    data = jwt.encode({"alg": "RS256"}, payload, private_key)
    assert data.count(b".") == 2

    claims = jwt.decode(data, pub_key)
    assert claims["name"] == "hi"

def test_use_jwe():
    payload = {"name": "hi"}
    private_key = read_file_path("rsa_private.pem")
    pub_key = read_file_path("rsa_public.pem")
    _jwt = JsonWebToken(["RSA-OAEP", "A256GCM"])
    data = _jwt.encode({"alg": "RSA-OAEP", "enc": "A256GCM"}, payload, pub_key)
    assert data.count(b".") == 4

    claims = _jwt.decode(data, private_key)
    assert claims["name"] == "hi"

def test_use_jwks():
    header = {"alg": "RS256", "kid": "abc"}
    payload = {"name": "hi"}
    private_key = read_file_path("jwks_private.json")
    pub_key = read_file_path("jwks_public.json")
    data = jwt.encode(header, payload, private_key)
    assert data.count(b".") == 2
    claims = jwt.decode(data, pub_key)
    assert claims["name"] == "hi"

def test_use_jwks_single_kid():
    """Test that jwks can be decoded if a kid for decoding is given and encoded data has no kid and only one key is set."""
    header = {"alg": "RS256"}
    payload = {"name": "hi"}
    private_key = read_file_path("jwks_single_private.json")
    pub_key = read_file_path("jwks_single_public.json")
    data = jwt.encode(header, payload, private_key)
    assert data.count(b".") == 2
    claims = jwt.decode(data, pub_key)
    assert claims["name"] == "hi"

def test_use_jwks_single_kid_keyset():
    """Test that jwks can be decoded if a kid for decoding is given and encoded data has no kid and a keyset with one key."""
    header = {"alg": "RS256"}
    payload = {"name": "hi"}
    private_key = read_file_path("jwks_single_private.json")
    pub_key = read_file_path("jwks_single_public.json")
    data = jwt.encode(header, payload, private_key)
    assert data.count(b".") == 2
    claims = jwt.decode(data, JsonWebKey.import_key_set(pub_key))
    assert claims["name"] == "hi"

def test_with_ec():
    payload = {"name": "hi"}
    private_key = read_file_path("secp521r1-private.json")
    pub_key = read_file_path("secp521r1-public.json")
    data = jwt.encode({"alg": "ES512"}, payload, private_key)
    assert data.count(b".") == 2

    claims = jwt.decode(data, pub_key)
    assert claims["name"] == "hi"

def test_with_zip_header():
    jwe = JsonWebEncryption()
    s = jwe.serialize_compact(
        {"alg": "RSA-OAEP", "enc": "A128CBC-HS256", "zip": "DEF"},
        "hello",
        read_file_path("rsa_public.pem"),
    )
    data = jwe.deserialize_compact(s, read_file_path("rsa_private.pem"))
    header, payload = data["header"], data["payload"]
    assert payload == b"hello"
    assert header["alg"] == "RSA-OAEP"

def test_aes_jwe():
    jwe = JsonWebEncryption()
    sizes = [128, 192, 256]
    _enc_choices = [
        "A128CBC-HS256",
        "A192CBC-HS384",
        "A256CBC-HS512",
        "A128GCM",
        "A192GCM",
        "A256GCM",
    ]
    for s in sizes:
        alg = f"A{s}KW"
        key = os.urandom(s // 8)
        for enc in _enc_choices:
            protected = {"alg": alg, "enc": enc}
            data = jwe.serialize_compact(protected, b"hello", key)
            rv = jwe.deserialize_compact(data, key)
            assert rv["payload"] == b"hello"

def test_aes_gcm_jwe():
    jwe = JsonWebEncryption()
    sizes = [128, 192, 256]
    _enc_choices = [
        "A128CBC-HS256",
        "A192CBC-HS384",
        "A256CBC-HS512",
        "A128GCM",
        "A192GCM",
        "A256GCM",
    ]
    for s in sizes:
        alg = f"A{s}GCMKW"
        key = os.urandom(s // 8)
        for enc in _enc_choices:
            protected = {"alg": alg, "enc": enc}
            data = jwe.serialize_compact(protected, b"hello", key)
            rv = jwe.deserialize_compact(data, key)
            assert rv["payload"] == b"hello"

def test_serialize_compact_allows_unknown_fields_in_header_while_private_fields_not_restricted():
    jwe = JsonWebEncryption()
    key = OKPKey.generate_key("X25519", is_private=True)

    protected = {"alg": "ECDH-ES+A128KW", "enc": "A128GCM", "foo": "bar"}

    data = jwe.serialize_compact(protected, b"hello", key)
    rv = jwe.deserialize_compact(data, key)
    assert rv["payload"] == b"hello"

def test_serialize_json_allows_unknown_fields_in_headers_while_private_fields_not_restricted():
    jwe = JsonWebEncryption()
    key = OKPKey.generate_key("X25519", is_private=True)

    protected = {"alg": "ECDH-ES+A128KW", "enc": "A128GCM", "foo1": "bar1"}
    unprotected = {"foo2": "bar2"}
    recipients = [{"header": {"foo3": "bar3"}}]
    header_obj = {
        "protected": protected,
        "unprotected": unprotected,
        "recipients": recipients,
    }

    data = jwe.serialize_json(header_obj, b"hello", key)
    rv = jwe.deserialize_json(data, key)
    assert rv["payload"] == b"hello"

def test_serialize_json_ignores_additional_members_in_recipients_elements():
    jwe = JsonWebEncryption()
    key = OKPKey.generate_key("X25519", is_private=True)

    protected = {"alg": "ECDH-ES+A128KW", "enc": "A128GCM"}

    data = jwe.serialize_compact(protected, b"hello", key)
    rv = jwe.deserialize_compact(data, key)
    assert rv["payload"] == b"hello"

def test_deserialize_json_allows_unknown_fields_in_headers_while_private_fields_not_restricted():
    jwe = JsonWebEncryption()
    key = OKPKey.generate_key("X25519", is_private=True)

    protected = {"alg": "ECDH-ES+A128KW", "enc": "A128GCM"}
    header_obj = {"protected": protected}

    data = jwe.serialize_json(header_obj, b"hello", key)

    data["unprotected"] = {"foo1": "bar1"}
    data["recipients"][0]["header"] = {"foo2": "bar2"}

    rv = jwe.deserialize_json(data, key)
    assert rv["payload"] == b"hello"

def test_deserialize_json_ignores_additional_members_in_recipients_elements():
    jwe = JsonWebEncryption()
    key = OKPKey.generate_key("X25519", is_private=True)

    protected = {"alg": "ECDH-ES+A128KW", "enc": "A128GCM"}
    header_obj = {"protected": protected}

    data = jwe.serialize_json(header_obj, b"hello", key)

    data["recipients"][0]["foo"] = "bar"

    data = jwe.serialize_compact(protected, b"hello", key)
    rv = jwe.deserialize_compact(data, key)
    assert rv["payload"] == b"hello"

def test_deserialize_json_ignores_additional_members_in_jwe_message():
    jwe = JsonWebEncryption()
    key = OKPKey.generate_key("X25519", is_private=True)

    protected = {"alg": "ECDH-ES+A128KW", "enc": "A128GCM"}
    header_obj = {"protected": protected}

    data = jwe.serialize_json(header_obj, b"hello", key)

    data["foo"] = "bar"

    data = jwe.serialize_compact(protected, b"hello", key)
    rv = jwe.deserialize_compact(data, key)
    assert rv["payload"] == b"hello"

def test_ecdh_es_jwe_in_direct_key_agreement_mode():
    jwe = JsonWebEncryption()
    key = {
        "kty": "EC",
        "crv": "P-256",
        "x": "weNJy2HscCSM6AEDTDg04biOvhFhyyWvOHQfeF_PxMQ",
        "y": "e8lnCO-AlStT-NJVX-crhB7QRYhiix03illJOVAOyck",
        "d": "VEmDZpDXXK8p8N0Cndsxs924q6nS1RXFASRl6BfUqdw",
    }

    for enc in [
        "A128CBC-HS256",
        "A192CBC-HS384",
        "A256CBC-HS512",
        "A128GCM",
        "A192GCM",
        "A256GCM",
    ]:
        protected = {"alg": "ECDH-ES", "enc": enc}
        data = jwe.serialize_compact(protected, b"hello", key)
        rv = jwe.deserialize_compact(data, key)
        assert rv["payload"] == b"hello"

def test_ecdh_es_jwe_json_serialization_single_recipient_in_direct_key_agreement_mode():
    jwe = JsonWebEncryption()
    key = OKPKey.generate_key("X25519", is_private=True)

    protected = {"alg": "ECDH-ES", "enc": "A128GCM"}
    header_obj = {"protected": protected}
    data = jwe.serialize_json(header_obj, b"hello", key)
    rv = jwe.deserialize_json(data, key)
    assert rv["payload"] == b"hello"

class TestRewrittenJWSNameCollisions:
    def test_compact_rsa(self):
            jws = JsonWebSignature()
            private_key = read_file_path("rsa_private.pem")
            public_key = read_file_path("rsa_public.pem")
            s = jws.serialize({"alg": "RS256"}, "hello", private_key)
            data = jws.deserialize(s, public_key)
            header, payload = data["header"], data["payload"]
            assert payload == b"hello"
            assert header["alg"] == "RS256"

            # can deserialize with private key
            data2 = jws.deserialize(s, private_key)
            assert data == data2

            ssh_pub_key = read_file_path("ssh_public.pem")
            with pytest.raises(errors.BadSignatureError):
                jws.deserialize(s, ssh_pub_key)


# Spec2Repo oracle - integration tests for authlib-fullrepro-001
# Source: selected tests from filter/generated_tests.py

import json

import os

import subprocess

import sys

import warnings

import pytest

from authlib.jose import BaseClaims

from authlib.jose import JWSHeader

from authlib.jose import JWTClaims

from authlib.jose import JsonWebEncryption

from authlib.jose import JsonWebKey

from authlib.jose import JsonWebSignature

from authlib.jose import JsonWebToken

from authlib.jose import KeySet

from authlib.jose import OctKey

from authlib.jose import errors

from authlib.jose import jwt

from authlib.jose.errors import JoseError

def test_overview_import_key_sign_encrypt_and_validate_claims():
    key = JsonWebKey.import_key("secret", {"kty": "oct", "kid": "overview"})
    signed = JsonWebSignature().serialize({"alg": "HS256"}, b"overview", key)
    verified = JsonWebSignature().deserialize(signed, key)
    enc_key = OctKey.generate_key(128, is_private=True)
    encrypted = JsonWebEncryption().serialize_compact(
        {"alg": "dir", "enc": "A128GCM"}, verified["payload"], enc_key
    )
    decrypted = JsonWebEncryption().deserialize_compact(encrypted, enc_key)
    claims = JWTClaims({"sub": decrypted["payload"].decode()}, {}, options={"sub": {"value": "overview"}})
    claims.validate(now=1)
    assert claims.sub == "overview"

def test_overview_preconfigured_jwt_round_trips_signed_claims():
    token = jwt.encode({"alg": "HS256"}, {"sub": "overview-jwt"}, "secret")
    claims = jwt.decode(token, "secret")
    claims.validate(now=1)
    assert claims.header["typ"] == "JWT"
    assert claims["sub"] == "overview-jwt"

def test_overview_high_level_objects_are_reusable_independently():
    jws = JsonWebSignature()
    jwe = JsonWebEncryption()
    key = OctKey.generate_key(128, is_private=True)
    signed = jws.serialize({"alg": "HS256"}, b"payload", "secret")
    encrypted = jwe.serialize_compact({"alg": "dir", "enc": "A128GCM"}, signed, key)
    decrypted = jwe.deserialize_compact(encrypted, key)
    assert jws.deserialize(decrypted["payload"], "secret")["payload"] == b"payload"

def test_scope_covers_jwk_jws_jwe_jwt_and_errors_together():
    jwk = JsonWebKey.import_key("secret", {"kty": "oct", "kid": "scope"})
    signed = JsonWebSignature().serialize({"alg": "HS256"}, b"scope", jwk)
    assert JsonWebSignature().deserialize(signed, jwk)["payload"] == b"scope"
    token = JsonWebToken(["HS256"]).encode({"alg": "HS256"}, {"kid": jwk.kid}, jwk)
    assert JsonWebToken(["HS256"]).decode(token, jwk)["kid"] == "scope"
    with pytest.raises(errors.DecodeError):
        JsonWebEncryption().parse_json("[]")

def test_installable_surface_exports_public_jose_objects_that_operate():
    token = jwt.encode({"alg": "HS256"}, {"sub": "installable"}, "secret")
    claims = JsonWebToken(["HS256"]).decode(token, "secret")
    assert claims["sub"] == "installable"
    assert isinstance(claims, JWTClaims)

def test_public_api_keyset_json_round_trips_through_import_key_set():
    key = OctKey.import_key("secret", {"kid": "public-api"})
    key_set = KeySet([key])
    imported = JsonWebKey.import_key_set(key_set.as_json())
    found = imported.find_by_kid("public-api")
    assert found["kid"] == "public-api"
    assert found["kty"] == "oct"

def test_public_api_custom_claims_class_receives_options_and_params():
    class CustomClaims(BaseClaims):
        pass

    token = JsonWebToken(["HS256"]).encode({"alg": "HS256"}, {"sub": "custom"}, "secret")
    claims = JsonWebToken(["HS256"]).decode(
        token,
        "secret",
        claims_cls=CustomClaims,
        claims_options={"sub": {"value": "custom"}},
        claims_params={"tenant": "demo"},
    )
    assert isinstance(claims, CustomClaims)
    assert claims.options["sub"]["value"] == "custom"
    assert claims.params["tenant"] == "demo"

def test_product_state_message_projection_round_trips_payload_and_header():
    jws = JsonWebSignature()
    serialized = jws.serialize({"alg": "HS256", "kid": "state-message"}, b"message", "secret")
    decoded = jws.deserialize(serialized, "secret")
    assert decoded["payload"] == b"message"
    assert decoded["header"]["kid"] == "state-message"

def test_product_state_token_projection_round_trips_header_and_claims():
    token = JsonWebToken(["HS256"]).encode({"alg": "HS256", "kid": "state-token"}, {"sub": "user"}, "secret")
    claims = JsonWebToken(["HS256"]).decode(token, "secret")
    assert claims.header["kid"] == "state-token"
    assert dict(claims) == {"sub": "user"}

def test_cross_view_private_key_export_import_preserves_public_projection():
    key = OctKey.generate_key(128, options={"kid": "cv-key"}, is_private=True)
    exported = key.as_dict(is_private=True)
    imported = JsonWebKey.import_key(exported)
    assert imported.as_dict()["kid"] == "cv-key"
    assert imported.as_dict()["kty"] == "oct"

def test_cross_view_keyset_selected_kid_is_visible_in_jwt_header():
    key = OctKey.import_key("secret", {"kid": "cv-jwt"})
    key_set = KeySet([key])
    token = JsonWebToken(["HS256"]).encode({"alg": "HS256"}, {"sub": "u"}, key_set)
    claims = JsonWebToken(["HS256"]).decode(token, key_set)
    assert claims.header["kid"] == "cv-jwt"
    assert claims["sub"] == "u"

def test_cross_view_jws_json_payload_survives_key_loader_round_trip():
    def load_key(header, payload):
        assert payload == b"cv-jws-json"
        return "secret"

    header = {"protected": {"alg": "HS256"}, "header": {"kid": "cv"}}
    serialized = JsonWebSignature().serialize_json(header, b"cv-jws-json", load_key)
    decoded = JsonWebSignature().deserialize_json(serialized, load_key)
    assert decoded["payload"] == b"cv-jws-json"
    assert decoded["header"]["kid"] == "cv"

def test_cross_view_jwe_json_payload_survives_recipient_key_round_trip():
    key = OctKey.generate_key(128, options={"kid": "cv-jwe"}, is_private=True)
    header = {
        "protected": {"alg": "dir", "enc": "A128GCM"},
        "recipients": [{"header": {"kid": "cv-jwe"}}],
    }
    serialized = JsonWebEncryption().serialize_json(header, b"cv-jwe-json", key)
    decoded = JsonWebEncryption().deserialize_json(serialized, ("cv-jwe", key))
    assert decoded["payload"] == b"cv-jwe-json"
    assert decoded["header"]["recipients"][0]["header"]["kid"] == "cv-jwe"

def test_cross_view_decoded_claims_expose_protected_header_values():
    token = JsonWebToken(["HS256"]).encode({"alg": "HS256", "kid": "cv-claims"}, {"sub": "u"}, "secret")
    claims = JsonWebToken(["HS256"]).decode(token, "secret")
    assert claims.header["kid"] == "cv-claims"
    assert claims["sub"] == "u"

def test_non_goals_jwt_remote_key_header_does_not_replace_supplied_key():
    token = JsonWebToken(["HS256"]).encode(
        {"alg": "HS256", "jku": "https://example.invalid/jwks"},
        {"sub": "local"},
        "secret",
    )
    claims = JsonWebToken(["HS256"]).decode(token, "secret")
    assert claims["sub"] == "local"
    assert claims.header["jku"] == "https://example.invalid/jwks"

def test_non_goals_jws_remote_header_is_observable_without_network_lookup():
    header = {"protected": {"alg": "HS256"}, "header": {"jku": "https://example.invalid/jwks"}}
    serialized = JsonWebSignature().serialize_json(header, b"local", "secret")
    decoded = JsonWebSignature().deserialize_json(serialized, "secret")
    assert decoded["payload"] == b"local"
    assert decoded["header"]["jku"] == "https://example.invalid/jwks"

def test_non_goals_jwe_remote_header_uses_supplied_local_key():
    key = OctKey.generate_key(128, is_private=True)
    header = {
        "protected": {"alg": "dir", "enc": "A128GCM"},
        "unprotected": {"jku": "https://example.invalid/jwks"},
        "recipients": [{}],
    }
    serialized = JsonWebEncryption().serialize_json(header, b"local", key)
    decoded = JsonWebEncryption().deserialize_json(serialized, key)
    assert decoded["payload"] == b"local"
    assert decoded["header"]["unprotected"]["jku"] == "https://example.invalid/jwks"

def test_invocation_from_authlib_jose_public_imports_work_in_subprocess():
    code = (
        "from authlib.jose import JsonWebSignature; "
        "s=JsonWebSignature().serialize({'alg':'HS256'}, b'x', 'secret'); "
        "assert JsonWebSignature().deserialize(s, 'secret')['payload'] == b'x'"
    )
    proc = subprocess.run([sys.executable, "-W", "ignore", "-c", code], text=True, env=os.environ.copy())
    assert proc.returncode == 0

def test_environment_subprocess_can_execute_symmetric_jws_round_trip():
    code = (
        "from authlib.jose import JsonWebSignature; "
        "jws=JsonWebSignature(); "
        "s=jws.serialize({'alg':'HS256'}, b'env', 'secret'); "
        "assert jws.deserialize(s, 'secret')['payload'] == b'env'"
    )
    proc = subprocess.run([sys.executable, "-W", "ignore", "-c", code], text=True, env=os.environ.copy())
    assert proc.returncode == 0

def test_environment_subprocess_can_execute_symmetric_jwe_round_trip():
    code = (
        "from authlib.jose import JsonWebEncryption, OctKey; "
        "key=OctKey.generate_key(128, is_private=True); "
        "jwe=JsonWebEncryption(); "
        "s=jwe.serialize_compact({'alg':'dir','enc':'A128GCM'}, b'env', key); "
        "assert jwe.deserialize_compact(s, key)['payload'] == b'env'"
    )
    proc = subprocess.run([sys.executable, "-W", "ignore", "-c", code], text=True, env=os.environ.copy())
    assert proc.returncode == 0

def test_evaluation_notes_observable_payload_and_header_are_asserted():
    serialized = JsonWebSignature().serialize({"alg": "HS256", "kid": "eval"}, b"payload", "secret")
    decoded = JsonWebSignature().deserialize(serialized, "secret")
    assert decoded["payload"] == b"payload"
    assert decoded["header"]["kid"] == "eval"
