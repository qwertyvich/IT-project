"""Справочная модель решения. Демонстрационные числа не являются испытаниями банка."""
from decimal import Decimal, InvalidOperation


def _number(value):
    """Недостоверное измерение не превращается в ноль или успешный результат."""
    if value is None or isinstance(value, bool):
        return None
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None
    return number if number.is_finite() else None


def _count(value):
    number = _number(value)
    if number is None or number < 0 or number != number.to_integral_value():
        return None
    return number


def _profile(value):
    if not isinstance(value, (tuple, list)) or len(value) != 3:
        return None
    counts = tuple(_count(item) for item in value)
    return None if None in counts else counts


def decision(a=None, b=None, qa=None, qb=None, *, same_staff=None,
             complete_logs=None, max_b_seconds=None, critical=None,
             mandatory_checks_passed=None, profile_a=None, profile_b=None):
    """Оценить свидетельства по заранее заданным нормам, не исполняя ПМИ.

    a/b — полный труд в человеко-минутах; qa/qb — верные результаты.
    profile_a/profile_b — состав предъявленных заданий: карта, перевод,
    кредитный договор (по 10 каждого вида); qa/qb — их верные исходы.
    mandatory_checks_passed — подтверждённое выполнение всех обязательных
    проверок И01–И23; None означает, что их исходы ещё не установлены.
    Полнота журналов и сопоставимость условий подтверждаются извне.
    """
    insufficient = {'verdict': 'недостаточно свидетельств'}
    critical_number = _count(critical)
    # Известный дефект нельзя скрыть отсутствием или порчей других измерений.
    if critical_number is not None and critical_number > 0:
        return {'verdict': 'не соответствует', 'reason': 'критическое нарушение'}
    if mandatory_checks_passed is False:
        return {'verdict': 'не соответствует', 'reason': 'обязательная проверка не пройдена'}
    if mandatory_checks_passed is not True:
        return {**insufficient, 'reason': 'исходы обязательных проверок не подтверждены'}

    a, b = _number(a), _number(b)
    qa, qb, critical_count = _count(qa), _count(qb), _count(critical)
    elapsed = _number(max_b_seconds)
    profile_a, profile_b = _profile(profile_a), _profile(profile_b)
    if None in (a, b, qa, qb, critical_count, elapsed, profile_a, profile_b):
        return {**insufficient, 'reason': 'отсутствующие или некорректные данные'}
    if a <= 0 or b < 0 or elapsed < 0:
        return {**insufficient, 'reason': 'некорректное измерение труда или времени'}
    if complete_logs is not True or same_staff is not True:
        return insufficient
    if qa > sum(profile_a) or qb > sum(profile_b):
        return {**insufficient, 'reason': 'число верных исходов превышает число заданий'}
    if profile_a != (10, 10, 10) or profile_b != (10, 10, 10):
        return {**insufficient, 'reason': 'некорректный состав сравнительных заданий'}
    if qa != 30:
        return {**insufficient, 'reason': 'неподтверждённая база сравнения'}
    if qb != 30 or elapsed > 120:
        return {'verdict': 'не соответствует',
                'reason': 'не достигнуты полнота или оперативность'}

    ua, ub = a / qa, b / qb
    reduction = (ua - ub) / ua * 100
    return {'verdict': 'соответствует' if ub <= Decimal('.80') * ua else 'не соответствует',
            'u_a': str(ua), 'u_b': str(ub), 'reduction_percent': str(reduction)}


def check_reference():
    args = dict(qa=30, qb=30, same_staff=True, complete_logs=True,
                max_b_seconds=120, critical=0, mandatory_checks_passed=True,
                profile_a=(10, 10, 10), profile_b=(10, 10, 10))
    reference = decision(180, 135, **args)
    assert reference['verdict'] == 'соответствует'
    assert Decimal(reference['reduction_percent']) == 25

    # Каждая строка задаёт отдельное наблюдаемое нарушение или пробел.
    cases = [
        (180, 144, {}, 'соответствует'),  # Ровно 20 %.
        (180, 145, {}, 'не соответствует'),
        (180, 135, {'max_b_seconds': 121}, 'не соответствует'),
        (180, 135, {'critical': 1}, 'не соответствует'),
        (180, 135, {'critical': '0.5'}, 'недостаточно свидетельств'),
        (None, 135, {'critical': 1, 'mandatory_checks_passed': None}, 'не соответствует'),
        (None, 135, {}, 'недостаточно свидетельств'),
        (180, 135, {'complete_logs': False}, 'недостаточно свидетельств'),
        (180, 135, {'same_staff': False}, 'недостаточно свидетельств'),
        (180, 135, {'qb': 29}, 'не соответствует'),
        (180, 135, {'qa': 29}, 'недостаточно свидетельств'),
        (180, 135, {'qa': 31}, 'недостаточно свидетельств'),
        (180, 135, {'qb': 31}, 'недостаточно свидетельств'),
        (180, 135, {'mandatory_checks_passed': None}, 'недостаточно свидетельств'),
        (180, 135, {'mandatory_checks_passed': False}, 'не соответствует'),
        # Быстрый отказ запросов не заменяет успешную обязательную проверку.
        (180, 135, {'max_b_seconds': 1, 'mandatory_checks_passed': False}, 'не соответствует'),
        (180, 135, {'profile_a': None}, 'недостаточно свидетельств'),
        (180, 135, {'profile_a': (30, 0, 0)}, 'недостаточно свидетельств'),
        (180, 135, {'profile_b': (30, 0, 0)}, 'недостаточно свидетельств'),
        (180, 135, {'profile_b': (10, -1, 21)}, 'недостаточно свидетельств'),
        (180, 135, {'profile_b': (10, 10)}, 'недостаточно свидетельств'),
        (-1, 135, {}, 'недостаточно свидетельств'),
        (180, -1, {}, 'недостаточно свидетельств'),
        (0, 135, {}, 'недостаточно свидетельств'),
        ('NaN', 135, {}, 'недостаточно свидетельств'),
        (180, 'Infinity', {}, 'недостаточно свидетельств'),
        (180, 135, {'max_b_seconds': -1}, 'недостаточно свидетельств'),
        (180, 135, {'max_b_seconds': 'NaN'}, 'недостаточно свидетельств'),
        (180, 135, {'critical': -1}, 'недостаточно свидетельств'),
        (180, 135, {'critical': 'NaN'}, 'недостаточно свидетельств'),
        (180, 135, {'qa': -1}, 'недостаточно свидетельств'),
        (180, 135, {'qb': 'Infinity'}, 'недостаточно свидетельств'),
        (180, 135, {'qb': '29.5'}, 'недостаточно свидетельств'),
        (180, 135, {'mandatory_checks_passed': 1}, 'недостаточно свидетельств'),
    ]
    for a, b, changes, expected in cases:
        assert decision(a, b, **{**args, **changes})['verdict'] == expected, changes
    return {'synthetic_formula_reference': reference,
            'boundary_cases': len(cases), 'bank_software_trials': False}
