#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module quản lý tài nguyên giao diện (icons, themes, etc.)
"""

import os
import base64
import logging
from io import BytesIO
from typing import Tuple, Dict, Any

from PIL import Image, ImageTk
import tkinter as tk

logger = logging.getLogger("keylogger.gui.resources")

class UIResources:
    """Quản lý tài nguyên giao diện như icons, hình ảnh, màu sắc"""

    # Icons mặc định được tạo bằng base64 để không phụ thuộc vào file bên ngoài
    ICONS = {
        "start": """
        iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAACXBIWXMAAAsTAAALEwEAmpwYAAAAv0lEQVR4nO2UQQrCMBBFX8UDTV0WehB33kbwHupCqHdSN3oQ3bvSkxREBJvJJGboKviXgZB58zNJgeE/MYBZ89X/hAKVQi3wOd0qoFKoFHZT4FG5GzhETmCTw/yIewF7oBYCwBzYnIFxFxq8Amahb4Fqh6VOOm7FMfVJg9JxK5e5V8BF8W9RdL8CG8XfZvKz9J6PwEHxpL03AiZW4DhEwTiHucQUWGaTJzQwLUIUuJjntBfomRk0zN5g8Ac8AEVuXz2RyLtJAAAAAElFTkSuQmCC
        """,
        "key": """
        iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAACXBIWXMAAAsTAAALEwEAmpwYAAAB2klEQVR4nLWVu2tUQRTGf3fXFQVNbAQDIirGQIyIhZUg+AdYCPZ2Vj7QRlIEbBQxhVgYUogWiqKid5VgpYIgohbGVvCB+EBUzOPuzOdiznI3d4NZ4164cDnznW++c86cb+6ARhYF3pKV1yawPDQRkVw9lKTzzpLY3wgM03w5KJd5Ib36HuCEFN+A78AnYElYWwLMAT5nclmXlRYPfGBnWJdmLnAaGHXGDgIvgKuSpA2K9RQfk7gCxoGxwBy0pXDdNu/JYH5nDPT9FLakvFIkLzQpZnU8IfcHBgDGMvl6j6CxHjcLDIyJbQlNZPJlESCGwXKRKTQ5K7YJuC2cE7GXwDnhgNgLYErBLYmdFTsutgCYkL2UZFVBNuiHwAl9m5QCGpL2YLe0bcntBTZmJEfUjwCXgZMKeNSMvZLsAqZlO6XcCfwG3oj9wz+RDvBEz8eSKwMX5HNLcq+lq9G9EvAmBrxPwJNakfzHQvn2CO+Rvc0sZbQrHdgL/ElB5lLLUDO4GxiSfk06t+ReLO0DYLPoTeA8MANJ/96YkndFyDntBQ6pn5+A9bLt96TmKPU9A1YBHcXdBi4q4BrgGXcL+irV0d0tdQOqZvSmtbkZVgKhY/7JMqvgPxPmqWOd1+b4AAAAAElFTkSuQmCC
        """,
        "stop": """
        iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAACXBIWXMAAAsTAAALEwEAmpwYAAABTElEQVR4nO2UPUsDQRCGn4goKIKFjRZaijaijWIhoo2VYGdjZ2MnWNvZ+QP8A4KVIFhYiYV2goWdlaA2gpWgIojfmYVLcrncJXdJITjwwt7uzDuz7MwuDPyfagYWgA1gD7gEXoC3EH2Fzz1wDKwCk0BdsyrEfAe4Axz8kRdgF5gFGvIhHwOOgfcYcZf8CJwBc0Cd12U+Bzx/QVTZ0JkLgQGgoKVIizM5uQr+7+9NiLfSjp6HjLyUSWAQ2AZGQtzlR3KlqA5gZCBqAj89njGPb1nGo3yZeNPAs9QrwGzEWCPAFjAO1MSMkwCLwHqQzxXoZcmqxF+BmfB8VgFMeBBRVdvIEpBVnypv/y1yVyC/fFqnYqEt28ZBNpUU6QKuA/Gi5EvAiUT/9JW4ohlgHtiUz6JC51XBYz5fTaxe4MqToynNMwXsxP0JDAUfAZ9Ufp8AAAAASUVORK5CYII=
        """,
        "settings": """
        iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAACXBIWXMAAAsTAAALEwEAmpwYAAACPklEQVR4nLWVTUhUURTHf+/NpE1FRR8gJUQfVLSINtG+KKRaFLWqoEWLWuTgprCoRbQoiGgfLQqiRdCmXUn0QUEURVQrIdtIUVFptIn5mDfT89xz4k7z5r0Zjejo4T3Ovf/zv+fec6/DmrPgwgZVOAQcAN8EDAfE76m4CzAswxDwxMJFgY7/F3p4FKodPHgbHI1B1xIUZ4PuVCgkIaJQEaCjHOaWYMzCVCLG9B4o+QeT3uCMQmWAY2tNnmJQnIKLdVAZhPFwHNcKa9SdVG0uVCTCOxZKA3AiCdczMFW0ylg4w6HROizOQnHAIZkQCDt4lZjgDlQtx8jWJ5inbTPR8G+Sn4L6JGgIMsHzOHMX0OQE2rrhbRgmUg7Zcb+rlYfgK8zlwKUm0K0bYTYXzu1dWSy6SzDth5eFMXvYaR+wNAvFwGwQpgqg2MWjMZv5bZYlzBZb1G2aUFtCxV+CdODgZwq6dsFcDnSWw7RrucuP0xfvmVgE6VPoT8PnLejdBk/DcNtCXwFc3g82CAMBeJ/Cbk94N8OhXrgTZtLDtBtG8qCqDyZySC8K+6R+sK73vA5OroOGOIVPDrYbqMgOQr2BKoPRTl2YDi5MRSAYcWgLwIcoDPvhiw+GrGVAfDPqZqzgfpyuwHjEjTFn4UTSGhcdPPE7GLbw2M3pGmR1QCfP4SBgbSA6JTGkRdv0BNWWVv1PjqHN4HbKGktLDG8UBmTfWdmHfgNUNKfz0YWUyAAAAABJRU5ErkJggg==
        """,
        "refresh": """
        iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAACXBIWXMAAAsTAAALEwEAmpwYAAACHElEQVR4nLWVT0iUQRTAf7PumqUVWodhSBnRwYIoPIQRXaJbEV07RASdunTqEHTtEkGXOtQhiKJDdYmCQoPAoD9QRIGHNDUMLa3d/X7fN9Nh5+/uu+vuuj0Y5s2b9+b9eW9mHmySjPqWbpQZE+N6I/WL4F8WOZJVZ7+KnAEZEVijCrU6V0ydaRW5KCLfVChUK8Dxr/A0QJfAaRO/bFZgvGPnigq3RGQsVPcDz8KwWgKDQZBbwpSADIhwCbgWZrguxBEVJkSZZb38eM5yXLXjkBJvW4KLWQd0eiXYE5XLKtx4ZbG9vbBvXcEpqypMqHJ7weJJqA4vO6yRxcxiLFRuqzC87HB/h4tUuuZJjYeQu3Hs7BOQ4qrD1aKhv8dDNrqpFDZoEKo8UOVBl8d4ZC2tIjR1uDwS4VLeNozDVnWZCqxlPudy9thhJOeyWsE0HwvCqAjTwFxDWGw0sKpvLVoRFqJ4jUbxQNxgKMhzhbvWCvWmzgn6+CuyqtJvlbOJJWG1cZKxJjARQD/w1gkTJsNQY5ibUHsE5IqjvPLhfZx/qyDLIofEsiMM+CzJpeoY61lkP/G1EziFyOBrizmqjEIrx/FIhOlC6K1S6FGLTz4Dq5ZC3mFHkyXDXvgS+NwTpf/P+Bdj2KCzQ5VLSYcR5KqIF25qP1qFx8A0wm9gzm2SGe1NlwAAAABJRU5ErkJggg==
        """,
        "export": """
        iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAACXBIWXMAAAsTAAALEwEAmpwYAAABP0lEQVR4nO2UP0vDUBTFf6+0NFi1IA5F3Bzd3NzEL9DP4Obo4ubg4Ofo5ifoILg6dHF1cdC1k+Li4GJbta0krTRpTF4SRBLyXtI6eOEuL5z87uHdcx+UVFKFwEHgGrgDnoExkNjhsZ17wD1wDRwuwjwAjJoiE+DM8Z9b7Qn4BJrAYV5znaOpcSZAVYj3LfeV1dSAyNH2rKYCXDiaL+DWcoeW+2G5tyKXwtxkxS07Oy96Fj+q4AzJZv4OTIAOMAD23bLQDFoZmVjPDdASsQ0RaxTtkptA31pEVwJYBB0Rm0vNw0K5IQfP1F7iTeBJxNvAJvACjJLf9t7ZWuBJYAf4Boai+f+/N6++kF1gCJwCI5tF7qwV+B3kCRGsAoc2i4Z935TzZ9kEVGHMpFy3v2lbWnfBYSlJ/QDzn8t74yLUzAAAAABJRU5ErkJggg==
        """,
        "save": """
        iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAACXBIWXMAAAsTAAALEwEAmpwYAAAA7ElEQVR4nO2UMUpDQRCGvyeYxsLCQkihWAhWFhY2WtjYir2VJxA8gUfIBWy8gJ5A0ih4ArGwE7EQC5NnZPGJsOw+eW/JFvlhYHdm9v92dmZhwJAzCXwAVqAVoEUmtMXQCvQDfAAT3ZYdAY/At8/iDngBHoB3n8UrcANMA6PAJHAGXPnsboBR4BDIgCefxRlQB8Z9HlfAHFDzrGeBeZ/1lS+DPeASaAA7wD6wCRwBp76+1fwRtKlwLLqlBkgdy/8dCxWe3c5BSlQSVEVUTKjAVQyUsVcEn8TzD3xvKWvhfGQQq7w1WY8fQ9JV1jThFVsAAAAASUVORK5CYII=
        """,
        "delete": """
        iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAACXBIWXMAAAsTAAALEwEAmpwYAAAAzklEQVR4nO2UzwnCQBCHvxEPgq9QsFRBEA+CHoKl2ICFWIaVWJGdCBZgA1bgn/fmMOvBhQQJuyZHwR98MLC7M7+Z2YUB/1QMXIEUyIADsONzOSjbMXAR/RUYdQ0PgBO1VsCyrUkjag4UHqM5MK0znQOPANMSWFBNjB4J8PRoD0DipdfeMcgpXLtbTKC9F33UNFO3Y0x1rpsG0ekc2LstmqHNGC3lqoB2ZQlM+jL3oQbWZ/pHwzCjLJCcHXD2afdCFoGGiQTpGNf97xnQO95ot3SuiHUkxQAAAABJRU5ErkJggg==
        """,
        "theme": """
        iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAACXBIWXMAAAsTAAALEwEAmpwYAAACQElEQVR4nL2VT2gTQRTGf28TKhQKhYJQsFAoFHoUL4LgUfDmRW+KFxE8CS3Fv1A8FC8evAn1JCiCePDmzZsXT0UQCh48FCzYQsHapGmatN0d3yzTsMnubiBIPnj7Zt+8+d43b94bWEctmb49KvIG6ANPVOTO2dY2Vw5XgB0i3DXCK+CoEU6LsEngs8LzdZnvKGxT4Q6F8aRQGKrwTZUnZzrbXC3AmoCKPAGO+z2P+LgR3hbClzaRIswB2xX2AftVoFAoqnJlqbkqkAHLRnhVFM79Hv8+g6QLHQPXjHA+Bd0Y9gHjKmyoAAswhLHPk06rSIfyEaW5UnjUP1AXc01EMlizxQhUxDW5scBrrlnvMPLmAWYqQPcIXhK8KP3mROSrwtEC1lJYXYGzwPfAYy6Qo+K6Kzr9SHV9BvWZcl4OqfLs9FcbA/OoZLd5XYaU/zNhP8DFsPnfk2/xmQyFQhgGP1MvSEshfgEb3YexZ0xxDwwnCPVgQiPcbwxD+EtZbR2E3RXGL5jByAh+BNKlLG6WJvJtEJcZZR6HkXtRIlwGbvpNeO6BDtJqHAeuAy/9xZoBlkd9i7K9v9v8ULU1mbUwk4vcXJD4O7EqPB+meDCQ/gZeA9/S9fEFv8hOa0Rnct/VYibFnZkr4lJhkQgTCXDHxa1jLcg4XRfLZYuuFWlG0jUxESmNvdNNOKTwOG7R3Ij3fRw/i9tXZwKAicBlhZfxvZ+JL/Y+F5dOD0vXpMJVn5nf1PscXqT18i3wB9wy9CLyGJ3lAAAAAElFTkSuQmCC
        """,
        "view": """
        iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAACXBIWXMAAAsTAAALEwEAmpwYAAABY0lEQVR4nO2UzyvDcRjHX9+PTDFyQHJxcXDm5OrkD0DOLhxc/QsOysmNciGHlZvkIC6KFJFckJ9N82Nmv+Z7+6y+mza+7Iw5vOrT83me9/v5vJ9Pz/MF/lWkOJQD7UA9kAWcAQGFgO+XEp3AtcRdYAnYBLYl7gCL6ncDtQp0J05I9EJ8pGgNGPOsD/v4/MZjCREfmPIB9gHPCj8CX+lUKdALXANfwAEQShUwAHxKvAzUJOlJ+JjENXHdqQAKgVmF74CNNH2bkkdmxSvSERTofAs4B64kLkoQdwNFPo6gb0D7W4WP7X+iLDGjgCujd4kP9t5Ux2uJI6nnfIWz41epLJe5l9h0Ww6MA++SOgUagSXgKT7FeZmAPWBG+6vAkaJhYBzIj00vc3qhcUz3sMbFCisPmI8nNtO8i10pTGP0OfCUDzxKnk2TuF6y25xfVHkm3ahYw5v/VfnASn9X/eN/AT+8rKexiO9xAAAAAElFTkSuQmCC
        """,
        "about": """
        iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAACXBIWXMAAAsTAAALEwEAmpwYAAACB0lEQVR4nLWVS0hUYRTHf3cURdTEC0SldOFChA6CmxDBNi2ibVBBbdy0iVYtokXuCjdtgyBo1SpoFUQgFUFUUJsWEURERFARFNjdzNHR+XfOd+Zqcxt1ZtJ/c+537nnnd77vfPceuG/K856rUAGI/7wJVW4Z49Ip/i+Z4wNgAgTUvRlCXGilHNVPKi3gCXCgHQJnYQgmEzCd9CQCTdoRsFM/aPLiGUShJx/QTtFDlKsUvQWLY5YOESAGiQosBCCE2d5OIZND8CiFJZCkzAaQCCm2oBTDXAjVFtwQpeqgGKfoVxXCFv3+mYJlNbiSgYsJrGw7BZcU4/PQCGF2UPD0/THNexrggaC//wg3NeoXiKFTlBrqFe8U7xTZDaJFEe1l2A+cN/BsCSuNAKI+mOfgwTRWYQY8bUKBccqBYugBYeqaZTAGFxUPb8CdZXhUBcbV5/vhUK9S1AvC1bW24aRi3jLsGoc8+rYW7TDlL9PwVHH/LRzuh/VHcE5RP9zeSYEx5cAybG+C8q3HK4yqyU3BJcWLj3CiH7IhzIJV+K7F3qFu/RL35WE6DusJ+Nt/C2FW7fwteDcMR7Ju3qf0Z9YNYfaF9kWYCGF8hLLvbOz7Esg2WEHr9yDq/vIFLbMJ3Z1qQbShU/dFQCn0fXAjbK3o+NcnpHXQf0r/AHib66/hS4J0AAAAAElFTkSuQmCC
        """,
        "search": """
        iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAACXBIWXMAAAsTAAALEwEAmpwYAAABJElEQVR4nO3UO0tDQRDF8Z8XEgVBFMTCwsJCSLATJIKVhY2tYOVnsLKz9EtYW1hZ2FloYScIiiJqYSFoYWHhC/GB5s/NLixhl2yiBDxwmJkzM/fu7ixs8Y9xA0zt8+yiHzrm0X/X0INaQlHjw38hSb0xTRMnwH7oi2giUCEsogpH2I3xMmtXKWlFl7tYC3mVmEIzFrGFG2xgdtAkSc8oJ6ZwjDbs4CoHNLAflplhJ76znA/RGWQvI6sEDNYXYy3XK0nRRDwewx2WsR3rRZzHexfFQlTURvz5mY9ZR0esl1IrqI16zLKmVTGjnXhO0ZyCOVGOMxI8oRv3KX5nCQZgB2cpflcTwHeao/RFDYqAIBgEeEMl5aB+iHKSAYU/5QVjdJsAXgFkx9Xd9vb1TgAAAABJRU5ErkJggg==
        """,
        "create": """
        iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAACXBIWXMAAAsTAAALEwEAmpwYAAAApElEQVR4nO2VQQ6CMBBFXxM3egEPoAcQj6gH8BSewwvUe3gJE+NCQlJDO6BdGF/SRdPh/8y0mbYw5Z90Ae6A1XfhANTAK/AdgDFtcg+sMsS70DNjkgCqzLhvGcOYlgCgpYZTj90RuFjDtcRuBrSK6FqitgKuiuhcorYTKPidXYzN1Yr/M9CUDdp/RZ+WRYnYjPmgcwkCKzFxCRZzBOqppvx3XlHDH+EJ2qYrCzUTfLwAAAAASUVORK5CYII=
        """,
        "bait": """
        iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAACXBIWXMAAAsTAAALEwEAmpwYAAACgElEQVR4nLWVTWhTQRDHfxutsTW1fmBVpH5AQfGDigqCngQRBBE8KVTxIli8qQdPTQ/eqidRRDyIJxURQSgiFkExKNYPlKJSFakGi4rGtGner52x++LLaxqS2gED+3Z25jez/51ZePUwUi+JL1LAI8nmPyj/Iccr4HtcMF0nwKgc34EHcbFGAAaB08DbOgHGgSfAduARMA7c1UBajDrAQeBTFmGgCmYEAm9l8hPgIOZV9+Js/L1Ue4CXQBswA5gJrAI2iN0A9IjKm9XtspPl5D3wRcTcmUr8t+aH1KaALuA6sBbzjE5gP/AJuAbsEYUW4JyC9QD7gCCy0BfAL9n/FXsP89ILwG3gKrBIPuVSexm4L8yOLMc54C5wTkTqQVYEjgDrFOgOcELJlwOfFXQbsEWBFVYr1gbgsfLVhKzU9AOLJZ5hoEmJR4UwqYktjfhOinHViWg5i/2W4GbAJpmOyOk1NSZqGTgtgW2SKjAPuAx8V5Bjol8R6QnVwYFsM2b0y4HpYloCNkrMAbMXGAGWSKqfgKPCyAF/NWeBI3KYEtNm4KnmDuE1mAm0y7ldVDq0OleBE8AQ8Epo92VyEZgvOXRLZquV3wGvBD+AYvhgVCshVDwC7AR+Y6uzS0xuWw5KRF3CdwO9QJ8c7mkPANuBZuA10A+cirzcwWoUREKyI8YV9JGYLZJuCGcF2IlcqwSzC/imJMWI6EOJLdLulYx2Kqb7wBL58DUJtZvqn+04LM3i3wDzVGl1tWLnTMvJ1tybvABcJP9VbcVaT/c6zQ5z1J6I0J7KmfwWNKwc5jnudbdPFYv/otfA06kC+Ou2TXM4TRL5ioG/lrGo7QP4GQH/A7y0JI7Jf9q7AAAAAElFTkSuQmCC
        """,
        "light_theme": """
        iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAACXBIWXMAAAsTAAALEwEAmpwYAAABg0lEQVR4nO2UPUsDQRDHf3dGYhEhKIKVhYX4AVJYWFj5AYJgaSPY+glS+QlSWNilFBQbC7URCzuxsBHURgsLmxx7msslm+SSmGDhwMHd7c7M/5+ZvYW+qkWjvgCspzwf03UuEz5o1mFURPIp8DcDkPRngOXQ6agU4B0YdlnGgSVgEMgBH8AVcKMxCWhoLBDH1Bdg1mwKgPiQ9Q4AZoBd4NRVB0wAJ8A+MA/cAXfOS1xpfQKmgHUP0PAAhcYI1UIfO3B+pM2MRTK4GRfXMQC2lnW9g9nKu4ZA7gGPWhcCwEzKiWK/4HUPFbM9Vu0PwEYAwOQegH0tsnkH8BJJX41AMbgGKg4gEpWs+zXmA1YlAYqupRDjrfBARddgq1IKAFUtzgOlhDLZ/qI7vlaSo2gd2AKuPUBVi9MeIBLrwF4Ih13bBLDnlxToHBj3AJHYcWsmSQXgXB+zZHEeUuC10cJ/qd0Kpvx1ayeKwBLQ6OU+uATWgGcHsAa86Ftqb2BPTz4J5BcawvOcq7rKywAAAABJRU5ErkJggg==
        """,
        "dark_theme": """
        iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAACXBIWXMAAAsTAAALEwEAmpwYAAABhUlEQVR4nO2Uv0vDQBTHPy/RxUFEcHFwcBCEOjk5Ojg46OCio4uLg9BF6OLioIODg5NDwcHVQQdHcXERnBxdJId/QGsiTRrSe4mJLfQKhZe8H+/7/b57754cQRklRLnM3FwT6G9g8MfSy3DwaMGcgzKoDPA5BuB0FnRrFCjTFgJFJ3gB3OjzlbY1IK9tV7/fgXo66UkYdYCf0t4AjrPk1oNPGh30gQ2gBnSAZ6CjCq3OZvRd1/EdWAEa4gsMbXYUYCaL0BqwA9TDBFuqpkgA5j0g1rbVwN+EOFCZ+PXrL3Oc2OMlLfRYjzXjQNsKnJZdYB/YdlZRTMRaJgCpLtBRdWbAOXCUANhUgHtAKvxEi33gJAGwD7xZgH0FEHK/5xZu4ETvgQBWgcsYwIUCCN13YDWIxQHawLKWqJAYsGFkMgI4TQCQIxfQBJo2HxKCa6iZ28BJQv4mNq9bCmDX9u0N+wD9P9oTuXVtzI7uZXWa06zeMUWbXM+NLb6XNKkPjYm9LnEFl6ILFv8zfgD2nDntVkAhZgAAAABJRU5ErkJggg==
        """,
        "cookie": """
        iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAACXBIWXMAAAsTAAALEwEAmpwYAAACSElEQVR4nO2UvWtTURiHn3tzW2s1ioKgCJJBEcSpaKciIjpYcHBRRFxE/BrEQUEn/wG3DnaSOgiKmzgILSJOTh0EC4pDBxHRqMH0I6a5974O8V6btne5XRz74uG8nJfzPud3zoGBDJKvlrYBt4CPQAuYAUYHIVsB5oA1YLHjOwFOZpVOOGMp5dRRYB44D4z7fHcC4uPAFHAhCt1LYMzA9azkM2nFvcBrYCdwDTgQM94DDgJXY8QfEilGgZMDGywCp+Jp+eIrBnYlLNQUOXoQg0XgFDDsTBdvgEOyQnc9d6cyvAQv5sVwSMKwVZ3qwzx9fJNKY6IZOFVDPYgkJFgHD0L3MmNsS5/3PwGb4Rjw3hjeCGNXm95MNjb8pN6YwbC5DdgPzHqrOoNkN/A5b+mWQzcbWNZlfcCkNwGsyG0lXLbAFb/R70UBnbfvgIc97l4KYdGjG/eWjVIJz3vLjm7+JeCNdF3+R2CFJDnAkOQV0Y2FXwxhKYAHnoXQLZJU0U6Qs2wDKkChA+BIxj5IynFwD5hO1h5YNXACuCMw24HJtGIOnAGGgDtSPgfTvs1p38wD290sXsU5hXtRlvYCL4BCZzGdZy6LwXiCMgeUe4r7ysZOg3aCKQXtFJnbRZ7Qpv+lQLVcw5kzoSsCp/okDlPiC6zlIDB5o2AZMaZPRdyqtXQOtJKgmvlzBn3gLXj5HwoQXANm0o+fJdqHVVLYdZXPxTduoFavgJ80N//yEm5yBhrkP6oflznLnB5qKMQAAAAASUVORK5CYII=
        """
    }

    # Hàm tiện ích để chuyển base64 thành hình ảnh
    @staticmethod
    def get_icon_image(
        icon_name: str, size: Tuple[int, int] = (20, 20)
    ) -> ImageTk.PhotoImage:
        """Tạo đối tượng PhotoImage từ mã base64 của icon
        
        Args:
            icon_name: Tên icon cần tạo
            size: Kích thước icon (width, height)
            
        Returns:
            ImageTk.PhotoImage: Đối tượng hình ảnh đã tạo
        """
        try:
            icon_data = UIResources.ICONS.get(icon_name, "")
            if not icon_data:
                # Trả về hình ảnh trống nếu không tìm thấy icon
                return ImageTk.PhotoImage(Image.new("RGBA", size, (0, 0, 0, 0)))

            # Chuyển base64 thành hình ảnh
            icon_data = icon_data.strip()
            img_data = base64.b64decode(icon_data)
            img = Image.open(BytesIO(img_data))
            img = img.resize(size, Image.Resampling.LANCZOS)
            return ImageTk.PhotoImage(img)
        except Exception as e:
            logger.error(f"Lỗi khi tạo icon {icon_name}: {e}")
            # Trả về hình ảnh trống nếu có lỗi
            return ImageTk.PhotoImage(Image.new("RGBA", size, (0, 0, 0, 0)))

    # Các bộ màu chủ đề
    THEMES = {
        "light": {
            "bg": "#f0f0f0",
            "fg": "#333333",
            "accent": "#0078d7",
            "highlight": "#e0f0ff",
            "success": "#28a745",
            "warning": "#ffc107",
            "error": "#dc3545",
            "btn_bg": "#e1e1e1",
            "btn_fg": "#333333",
            "btn_hover": "#d1d1d1",
            "entry_bg": "#ffffff",
            "entry_fg": "#333333",
            "scrollbar": "#c1c1c1",
        },
        "dark": {
            "bg": "#2b2b2b",
            "fg": "#e0e0e0",
            "accent": "#0078d7",
            "highlight": "#1e3a5f",
            "success": "#28a745",
            "warning": "#ffc107",
            "error": "#dc3545",
            "btn_bg": "#3c3c3c",
            "btn_fg": "#e0e0e0",
            "btn_hover": "#4c4c4c",
            "entry_bg": "#3c3c3c",
            "entry_fg": "#e0e0e0",
            "scrollbar": "#555555",
        },
    }

    @staticmethod
    def get_theme(name: str) -> Dict[str, str]:
        """Lấy bảng màu của theme cụ thể
        
        Args:
            name: Tên theme ('light' hoặc 'dark')
            
        Returns:
            Dict[str, str]: Từ điển các mã màu của theme
        """
        return UIResources.THEMES.get(name, UIResources.THEMES["light"])