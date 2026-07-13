"""
minipackaging.py - A dependency-free Python module for parsing and evaluating
Python package metadata (PEP 440 versions, PEP 508 requirements, environment markers).
"""

import re
import sys
import os
import platform
from typing import Optional, Union, List, Tuple, Any, Set, Dict


# =============================================================================
# Exceptions
# =============================================================================

class InvalidVersion(ValueError):
    """Raised when a version string is invalid."""
    pass


class InvalidSpecifier(ValueError):
    """Raised when a specifier string is invalid."""
    pass


class InvalidRequirement(ValueError):
    """Raised when a requirement string is invalid."""
    pass


class InvalidMarker(ValueError):
    """Raised when a marker string is invalid."""
    pass


class UndefinedEnvironmentName(ValueError):
    """Raised when a required environment variable is missing."""
    pass


# =============================================================================
# Version (PEP 440)
# =============================================================================

class Version:
    """
    Parse and compare PEP 440 version strings.
    
    Supports:
    - Epoch: N!
    - Release: N.N.N...
    - Pre-release: a, alpha, b, beta, rc, c, pre, preview
    - Post-release: post, rev, r
    - Dev release: dev
    - Local version: +label
    """
    
    # Pre-release mappings
    _PRE_RELEASE_MAP = {
        'a': 'a', 'alpha': 'a',
        'b': 'b', 'beta': 'b',
        'rc': 'rc', 'c': 'rc', 'pre': 'rc', 'preview': 'rc',
    }
    
    # Post-release mappings
    _POST_RELEASE_MAP = {
        'post': 'post', 'rev': 'post', 'r': 'post',
    }
    
    def __init__(self, text: str):
        if not isinstance(text, str):
            raise InvalidVersion(f"Version must be a string, got {type(text).__name__}")
        
        self._original = text
        self._epoch = 0
        self._release: Tuple[int, ...] = ()
        self._pre: Optional[Tuple[str, int]] = None  # (phase, number)
        self._post: Optional[int] = None
        self._dev: Optional[int] = None
        self._local: Optional[Tuple[Union[int, str], ...]] = None
        
        self._parse(text)
    
    def _parse(self, text: str) -> None:
        """Parse the version string into components."""
        original = text
        text = text.strip().lower()
        
        if not text:
            raise InvalidVersion(f"Empty version string: {original}")
        
        pos = 0
        
        # Epoch: N!
        match = re.match(r'^(\d+)!', text)
        if match:
            self._epoch = int(match.group(1))
            pos = match.end()
        
        # Get the rest after epoch
        rest = text[pos:]
        if not rest:
            raise InvalidVersion(f"Invalid version string: {original}")
        
        # Split on local version first
        local_match = re.search(r'[\+\-\.]', rest)
        local_start = None
        if local_match:
            # Find the + sign for local version
            plus_match = re.search(r'\+', rest)
            if plus_match:
                local_start = plus_match.start()
        
        if local_start is not None:
            main_part = rest[:local_start]
            local_part = rest[local_start + 1:]  # Skip the +
            self._local = self._parse_local(local_part, original)
        else:
            main_part = rest
        
        # Now parse main part: release, pre, post, dev
        self._parse_main(main_part, original)
    
    def _parse_main(self, text: str, original: str) -> None:
        """Parse release, pre-release, post-release, and dev portions."""
        if not text:
            raise InvalidVersion(f"Invalid version string: {original}")
        
        # Pattern to extract components
        # Release segment is required
        release_match = re.match(r'^(\d+(?:\.\d+)*)', text)
        if not release_match:
            raise InvalidVersion(f"Invalid version string: {original}")
        
        release_str = release_match.group(1)
        self._release = tuple(int(x) for x in release_str.split('.'))
        pos = release_match.end()
        remaining = text[pos:]
        
        # Check for dev release (can come before post/pre in some positions)
        # Handle both .devN and devN formats
        dev_match = re.match(r'(\.?)(dev)(\d*)', remaining, re.IGNORECASE)
        if dev_match:
            self._dev = int(dev_match.group(3)) if dev_match.group(3) else 0
            remaining = remaining[dev_match.end():]
        
        # Check for pre-release - handle both .aN and aN formats
        # Order alternatives from longest to shortest to match 'alpha' before 'a'
        pre_match = re.match(r'(\.?)(alpha|beta|preview|pre|a|b|c|rc)(\d*)', remaining, re.IGNORECASE)
        if pre_match:
            phase = self._PRE_RELEASE_MAP[pre_match.group(2).lower()]
            self._pre = (phase, int(pre_match.group(3)) if pre_match.group(3) else 0)
            remaining = remaining[pre_match.end():]
        
        # Check for post-release - handle both .postN and postN formats
        # Order alternatives from longest to shortest
        post_match = re.match(r'(\.?)(post|rev|r)(\d*)', remaining, re.IGNORECASE)
        if post_match:
            self._post = int(post_match.group(3)) if post_match.group(3) else 0
            remaining = remaining[post_match.end():]
        
        # Check for dev release (can also come after post)
        if self._dev is None:
            dev_match2 = re.match(r'(\.?)(dev)(\d*)', remaining, re.IGNORECASE)
            if dev_match2:
                self._dev = int(dev_match2.group(3)) if dev_match2.group(3) else 0
                remaining = remaining[dev_match2.end():]
        
        # Any remaining non-whitespace is invalid
        remaining = remaining.strip()
        if remaining:
            raise InvalidVersion(f"Invalid version string: {original}")
    
    def _parse_local(self, text: str, original: str) -> Tuple[Union[int, str], ...]:
        """Parse local version label."""
        if not text:
            raise InvalidVersion(f"Invalid local version in: {original}")
        
        # Split on ., -, or _
        parts = re.split(r'[\.\-\.]', text)
        result: List[Union[int, str]] = []
        
        for part in parts:
            if not part:
                continue
            # Try to parse as int
            if re.match(r'^\d+$', part):
                result.append(int(part))
            else:
                result.append(part.lower())
        
        if not result:
            raise InvalidVersion(f"Invalid local version in: {original}")
        
        return tuple(result)
    
    def __str__(self) -> str:
        """Return canonical string representation."""
        parts = []
        
        # Epoch
        if self._epoch:
            parts.append(f"{self._epoch}!")
        
        # Release - trim trailing zeros but keep at least one segment
        release = list(self._release)
        while len(release) > 1 and release[-1] == 0:
            release.pop()
        parts.append('.'.join(str(x) for x in release))
        
        # Pre-release (dot before pre-release)
        if self._pre:
            parts.append(f".{self._pre[0]}{self._pre[1]}")
        
        # Post-release (dot before post-release)
        if self._post is not None:
            parts.append(f".post{self._post}")
        
        # Dev release (dot before dev)
        if self._dev is not None:
            parts.append(f".dev{self._dev}")
        
        # Local version
        if self._local:
            parts.append('+' + '.'.join(str(x) for x in self._local))
        
        return ''.join(parts)
    
    def __repr__(self) -> str:
        return f"Version('{str(self)}')"
    
    def _cmp_key(self) -> Tuple:
        """
        Generate sorting key for comparison.
        
        Order: epoch, release tuple, dev, pre, final, post, local
        Dev releases: before pre-releases and final releases
        Pre releases: before final
        Post releases: after final
        """
        # Normalize release for comparison - strip trailing zeros
        release = list(self._release)
        while len(release) > 1 and release[-1] == 0:
            release.pop()
        
        # Dev release - dev releases sort before everything (pre and final)
        # Use 0 for is_dev to sort before non-dev (1)
        dev_sort = (0 if self._dev is not None else 1, self._dev if self._dev is not None else 0)
        
        # Pre-release sorting
        # None means no pre-release (final release)
        # Pre-releases sort before final releases but after dev releases
        if self._pre:
            pre_sort = (0, self._pre[0], self._pre[1])  # 0 = is pre
        else:
            pre_sort = (1, '', 0)  # 1 = not pre (final)
        
        # Post release - post releases sort after final releases
        if self._post is not None:
            post_sort = (1, self._post)  # 1 = has post
        else:
            post_sort = (0, 0)  # 0 = no post
        
        # Local version
        if self._local:
            local_sort = (1, self._local)  # 1 = has local
        else:
            local_sort = (0, ())
        
        return (
            self._epoch,
            tuple(release),
            dev_sort,      # (is_dev, dev_number) - dev (0) sorts before non-dev (1)
            pre_sort,      # (is_pre_phase, phase, number) - pre (0) sorts before final (1)
            post_sort,     # (has_post, post_number) - post (1) sorts after no-post (0)
            local_sort,    # (has_local, local_tuple)
        )
    
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return self._cmp_key() == other._cmp_key()
    
    def __hash__(self) -> int:
        return hash(self._cmp_key())
    
    def __lt__(self, other: Any) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return self._cmp_key() < other._cmp_key()
    
    def __le__(self, other: Any) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return self._cmp_key() <= other._cmp_key()
    
    def __gt__(self, other: Any) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return self._cmp_key() > other._cmp_key()
    
    def __ge__(self, other: Any) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return self._cmp_key() >= other._cmp_key()


# =============================================================================
# SpecifierSet
# =============================================================================

class SpecifierSet:
    """
    Parse and check version specifier sets.
    
    Supported operators: ==, !=, >=, <=, >, <, ~=
    Wildcard .* for == and !=
    ~= means compatible release
    """
    
    _OPERATORS = {'==', '!=', '>=', '<=', '>', '<', '~='}
    
    def __init__(self, text: str = ""):
        if not isinstance(text, str):
            raise InvalidSpecifier(f"SpecifierSet must be a string, got {type(text).__name__}")
        
        self._original = text
        self._clauses: List[Tuple[str, Version]] = []
        
        if text.strip():
            self._parse(text)
    
    def _parse(self, text: str) -> None:
        """Parse comma-separated specifier clauses."""
        text = text.strip()
        
        # Split by comma
        clauses = [c.strip() for c in text.split(',')]
        
        for clause in clauses:
            if not clause:
                continue
            
            # Extract operator and version
            match = re.match(r'^(==|!=|>=|<=|>|<|~=)\s*(.+)$', clause)
            if not match:
                raise InvalidSpecifier(f"Invalid specifier clause: {clause}")
            
            op = match.group(1)
            version_str = match.group(2).strip()
            
            if op in ('==', '!='):
                # May have wildcard
                if version_str.endswith('.*'):
                    version_str = version_str[:-2]
                    # Validate version without wildcard
                    try:
                        version = Version(version_str)
                    except InvalidVersion as e:
                        raise InvalidSpecifier(f"Invalid version in specifier: {clause}")
                    self._clauses.append((op, version, True))  # True = has wildcard
                    continue
            
            try:
                version = Version(version_str)
            except InvalidVersion as e:
                raise InvalidSpecifier(f"Invalid version in specifier: {clause}")
            
            self._clauses.append((op, version, False))
    
    def contains(self, version: Union[str, Version], prereleases: Optional[bool] = None) -> bool:
        """
        Check if version satisfies all clauses.
        
        Args:
            version: Version string or Version object
            prereleases: If True, include pre-releases. If False, exclude them.
                        If None, use version's natural status.
        """
        if isinstance(version, str):
            version = Version(version)
        
        # Check if version is a pre-release or dev release
        is_pre_or_dev = (version._pre is not None or version._dev is not None)
        
        # Determine if we should check prereleases
        check_prereleases = prereleases
        if prereleases is None:
            # Check if any specifier mentions a pre-release
            for op, ver, _ in self._clauses:
                if ver._pre is not None or ver._dev is not None:
                    check_prereleases = True
                    break
            else:
                # No prerelease versions mentioned, exclude prereleases
                check_prereleases = False
        
        # If this is a pre-release and we're not checking them, fail immediately
        if is_pre_or_dev and check_prereleases is False:
            return False
        
        for clause in self._clauses:
            if len(clause) == 3:
                # Has wildcard
                op = clause[0]
                spec_version = clause[1]
                has_wildcard = clause[2]
            else:
                op = clause[0]
                spec_version = clause[1]
                has_wildcard = False
            
            if not self._check_clause(op, spec_version, has_wildcard, version):
                return False
        
        return True
    
    def _check_clause(self, op: str, spec_version: Version, has_wildcard: bool, version: Version) -> bool:
        """Check a single specifier clause."""
        if op == '==':
            if has_wildcard:
                # Match prefix
                return self._match_prefix(spec_version, version)
            return version == spec_version
        elif op == '!=':
            if has_wildcard:
                return not self._match_prefix(spec_version, version)
            return version != spec_version
        elif op == '>=':
            return version >= spec_version
        elif op == '<=':
            return version <= spec_version
        elif op == '>':
            return version > spec_version
        elif op == '<':
            return version < spec_version
        elif op == '~=':
            return self._compatible_release(spec_version, version)
        
        return False
    
    def _match_prefix(self, spec_version: Version, version: Version) -> bool:
        """Match version against prefix wildcard."""
        spec_release = spec_version._release
        version_release = version._release
        
        # Check if version starts with spec prefix
        if len(version_release) < len(spec_release):
            return False
        
        return version_release[:len(spec_release)] == spec_release
    
    def _compatible_release(self, spec_version: Version, version: Version) -> bool:
        """
        Check compatible release (~=).
        
        ~=X.Y means >=X.Y, <(X+1).0 for two-segment
        ~=X.Y.Z means >=X.Y.Z, <X.(Y+1).0 for three-segment
        """
        if version < spec_version:
            return False
        
        spec_release = spec_version._release
        version_release = version._release
        
        if len(spec_release) < 2:
            return False  # ~= needs at least X.Y
        
        # Upper bound: increment second-to-last component
        upper = list(spec_release[:-1])
        upper[-1] += 1
        upper_bound = Version('.'.join(str(x) for x in upper))
        
        # Also ensure epoch matches
        if version._epoch != spec_version._epoch:
            return False
        
        return version < upper_bound
    
    def __str__(self) -> str:
        """Return canonical string representation."""
        if not self._clauses:
            return ""
        
        parts = []
        for clause in self._clauses:
            if len(clause) == 3:
                op, ver, has_wildcard = clause
                if has_wildcard:
                    parts.append(f"{op}{ver}.*")
                else:
                    parts.append(f"{op}{ver}")
            else:
                op, ver = clause
                parts.append(f"{op}{ver}")
        
        return ','.join(parts)
    
    def __repr__(self) -> str:
        return f"SpecifierSet('{str(self)}')"
    
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, SpecifierSet):
            return NotImplemented
        return str(self) == str(other)
    
    def __hash__(self) -> int:
        return hash(str(self))


# =============================================================================
# Requirement (PEP 508)
# =============================================================================

class Requirement:
    """
    Parse PEP 508 requirement strings.
    
    Format: name[extras] specifier ; marker
    Or: name[extras] @ url ; marker
    """
    
    # Name/extras pattern: start/end with letter/digit, contain letter/digit/./_/-
    _NAME_PATTERN = re.compile(r'^[a-zA-Z0-9]([a-zA-Z0-9._-]*[a-zA-Z0-9])?$|^[a-zA-Z0-9]$')
    
    def __init__(self, text: str):
        if not isinstance(text, str):
            raise InvalidRequirement(f"Requirement must be a string, got {type(text).__name__}")
        
        self._original = text
        self._name: str = ""
        self._extras: Set[str] = set()
        self._specifier = SpecifierSet("")
        self._url: Optional[str] = None
        self._marker: Optional[Marker] = None
        
        self._parse(text)
    
    def _parse(self, text: str) -> None:
        """Parse the requirement string."""
        text = text.strip()
        original = text
        
        if not text:
            raise InvalidRequirement(f"Empty requirement string: {original}")
        
        # Split by semicolon for marker
        if ';' in text:
            marker_idx = text.index(';')
            marker_text = text[marker_idx + 1:].strip()
            text = text[:marker_idx].strip()
            
            if marker_text:
                self._marker = Marker(marker_text)
        
        # Check for URL (@ symbol)
        url_match = re.search(r'\s*@\s*(.+)$', text)
        if url_match:
            self._url = url_match.group(1).strip()
            text = text[:url_match.start()].strip()
        
        # Now parse name[extras] and optional specifier
        # Name pattern
        name_match = re.match(r'^([a-zA-Z0-9]([a-zA-Z0-9._-]*[a-zA-Z0-9])?|[a-zA-Z0-9])', text)
        if not name_match:
            raise InvalidRequirement(f"Invalid package name in: {original}")
        
        raw_name = name_match.group(0)
        # Validate name
        if not self._NAME_PATTERN.match(raw_name):
            raise InvalidRequirement(f"Invalid package name: {raw_name}")
        
        # Normalize name
        self._name = raw_name.lower().replace('_', '-')
        pos = name_match.end()
        remaining = text[pos:]
        
        # Check for extras [foo,bar]
        extras_match = re.match(r'^\[([^\]]*)\]', remaining)
        if extras_match:
            extras_str = extras_match.group(1)
            if extras_str.strip():
                for extra in extras_str.split(','):
                    extra = extra.strip()
                    if not extra:
                        raise InvalidRequirement(f"Empty extra in: {original}")
                    if not self._NAME_PATTERN.match(extra):
                        raise InvalidRequirement(f"Invalid extra name: {extra}")
                    self._extras.add(extra.lower().replace('_', '-'))
            remaining = remaining[extras_match.end():]
        
        remaining = remaining.strip()
        remaining = remaining.strip()  # Handle trailing whitespace
        
        # What's left should be specifier (or empty)
        if remaining:
            if self._url:
                # Can't have both URL and specifier
                raise InvalidRequirement(f"Cannot have both URL and version specifier: {original}")
            
            try:
                self._specifier = SpecifierSet(remaining)
            except InvalidSpecifier as e:
                raise InvalidRequirement(f"Invalid specifier in requirement: {original}")
    
    @property
    def name(self) -> str:
        """Normalized package name."""
        return self._name
    
    @property
    def extras(self) -> Set[str]:
        """Set of normalized extra names."""
        return self._extras.copy()
    
    @property
    def specifier(self) -> SpecifierSet:
        """Version specifier set."""
        return self._specifier
    
    @property
    def url(self) -> Optional[str]:
        """Direct URL if present."""
        return self._url
    
    @property
    def marker(self) -> Optional[Marker]:
        """Environment marker if present."""
        return self._marker
    
    def __str__(self) -> str:
        """Return canonical requirement string."""
        parts = [self._name]
        
        if self._extras:
            sorted_extras = sorted(self._extras)
            parts.append('[' + ','.join(sorted_extras) + ']')
        
        if self._url:
            parts.append(f' @ {self._url}')
        elif str(self._specifier):
            parts.append(str(self._specifier))
        
        if self._marker:
            parts.append(f' ; {str(self._marker)}')
        
        return ''.join(parts)
    
    def __repr__(self) -> str:
        return f"Requirement('{str(self)}')"
    
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Requirement):
            return NotImplemented
        
        return (
            self._name == other._name and
            self._extras == other._extras and
            self._specifier == other._specifier and
            self._url == other._url and
            self._marker == other._marker
        )
    
    def __hash__(self) -> int:
        return hash((self._name, frozenset(self._extras), self._specifier, self._url, self._marker or ''))


# =============================================================================
# Marker
# =============================================================================

class Marker:
    """
    Parse and evaluate environment markers.
    
    Supported variables: python_version, python_full_version, os_name,
    sys_platform, platform_machine, platform_system, platform_release,
    platform_version, platform_python_implementation, implementation_name,
    implementation_version, extra
    
    Operators: ==, !=, <, <=, >, >=, in, not in
    Boolean: parentheses, and, or
    """
    
    _VARIABLES = {
        'python_version', 'python_full_version', 'os_name', 'sys_platform',
        'platform_machine', 'platform_system', 'platform_release',
        'platform_version', 'platform_python_implementation',
        'implementation_name', 'implementation_version', 'extra'
    }
    
    _OPERATORS = {'==', '!=', '<', '<=', '>', '>=', 'in', 'not', 'and', 'or'}
    
    def __init__(self, text: str):
        if not isinstance(text, str):
            raise InvalidMarker(f"Marker must be a string, got {type(text).__name__}")
        
        self._original = text
        self._parsed: Optional[Any] = None  # Parsed AST representation
        
        self._parse(text)
    
    def _parse(self, text: str) -> None:
        """Parse the marker expression into an AST."""
        text = text.strip()
        original = text
        
        if not text:
            raise InvalidMarker(f"Empty marker string: {original}")
        
        # Tokenize
        tokens = self._tokenize(text, original)
        
        # Parse with precedence: OR < AND < comparisons
        self._parsed = self._parse_or(tokens, original)
    
    def _tokenize(self, text: str, original: str) -> List[Tuple[str, Any]]:
        """Tokenize marker expression."""
        tokens: List[Tuple[str, Any]] = []
        pos = 0
        text = text.strip()
        
        while pos < len(text):
            # Skip whitespace
            while pos < len(text) and text[pos] in ' \t':
                pos += 1
            
            if pos >= len(text):
                break
            
            # Parentheses
            if text[pos] == '(':
                tokens.append(('LPAREN', '('))
                pos += 1
                continue
            elif text[pos] == ')':
                tokens.append(('RPAREN', ')'))
                pos += 1
                continue
            
            # String literals
            if text[pos] in '"\'':
                quote = text[pos]
                pos += 1
                start = pos
                while pos < len(text) and text[pos] != quote:
                    if text[pos] == '\\' and pos + 1 < len(text):
                        pos += 2
                    else:
                        pos += 1
                
                if pos >= len(text):
                    raise InvalidMarker(f"Unterminated string in: {original}")
                
                string_val = text[start:pos]
                # Handle escape sequences
                string_val = string_val.replace('\\"', '"').replace("\\'", "'").replace('\\\\', '\\')
                tokens.append(('STRING', string_val))
                pos += 1
                continue
            
            # Operators (check multi-char first)
            op_match = re.match(r'^(==|!=|<=|>=|not in|in|[<>=!])', text[pos:])
            if op_match:
                op = op_match.group(0)
                tokens.append(('OP', op))
                pos += len(op)
                continue
            
            # Boolean operators (check before variable names)
            if text[pos:].startswith('and'):
                tokens.append(('OP', 'and'))
                pos += 3
                continue
            if text[pos:].startswith('or'):
                tokens.append(('OP', 'or'))
                pos += 2
                continue
            
            # Variable names
            var_match = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*)', text[pos:])
            if var_match:
                var = var_match.group(1)
                if var not in self._VARIABLES:
                    raise InvalidMarker(f"Unknown variable '{var}' in: {original}")
                tokens.append(('VAR', var))
                pos += len(var)
                continue
            
            raise InvalidMarker(f"Unexpected character '{text[pos]}' at position {pos} in: {original}")
        
        return tokens
    
    def _parse_or(self, tokens: List[Tuple[str, Any]], original: str) -> Any:
        """Parse OR expressions (lowest precedence)."""
        left = self._parse_and(tokens, original)
        
        while tokens and tokens[0] == ('OP', 'or'):
            tokens.pop(0)
            right = self._parse_and(tokens, original)
            left = ('OR', left, right)
        
        return left
    
    def _parse_and(self, tokens: List[Tuple[str, Any]], original: str) -> Any:
        """Parse AND expressions."""
        left = self._parse_comparison(tokens, original)
        
        while tokens and tokens[0] == ('OP', 'and'):
            tokens.pop(0)
            right = self._parse_comparison(tokens, original)
            left = ('AND', left, right)
        
        return left
    
    def _parse_comparison(self, tokens: List[Tuple[str, Any]], original: str) -> Any:
        """Parse comparison expressions."""
        if not tokens:
            raise InvalidMarker(f"Unexpected end of marker: {original}")
        
        # Handle parentheses
        if tokens[0][0] == 'LPAREN':
            tokens.pop(0)
            result = self._parse_or(tokens, original)
            if not tokens or tokens[0][0] != 'RPAREN':
                raise InvalidMarker(f"Missing closing parenthesis in: {original}")
            tokens.pop(0)
            return result
        
        # Left side (variable)
        if tokens[0][0] != 'VAR':
            raise InvalidMarker(f"Expected variable, got {tokens[0]} in: {original}")
        
        left_var = tokens.pop(0)[1]
        
        # Operator
        if not tokens or tokens[0][0] != 'OP':
            raise InvalidMarker(f"Expected comparator in: {original}")
        
        full_op = tokens.pop(0)[1]
        
        # Handle 'not in'
        if full_op == 'not':
            if not tokens or tokens[0] != ('OP', 'in'):
                raise InvalidMarker(f"Expected 'in' after 'not' in: {original}")
            tokens.pop(0)
            full_op = 'not in'
        
        # Right side (string value)
        if not tokens:
            raise InvalidMarker(f"Expected value after operator in: {original}")
        
        if tokens[0][0] == 'STRING':
            right_val = tokens.pop(0)[1]
            return ('CMP', left_var, full_op, right_val)
        else:
            raise InvalidMarker(f"Expected string value, got {tokens[0]} in: {original}")
    
    def evaluate(self, environment: Optional[Dict[str, str]] = None, requested_extras: Optional[List[str]] = None) -> bool:
        """
        Evaluate the marker against an environment.
        
        Args:
            environment: Dict of environment variables. Defaults to default_environment().
            requested_extras: List of requested extras for 'extra' variable.
        
        Returns:
            True if marker applies, False otherwise.
        """
        if environment is None:
            environment = default_environment()
        else:
            # Copy to avoid mutation
            environment = dict(environment)
        
        if requested_extras is None:
            requested_extras = []
        
        # Normalize requested extras
        normalized_extras = [e.lower().replace('_', '-') for e in requested_extras]
        
        return self._evaluate_node(self._parsed, environment, normalized_extras)
    
    def _evaluate_node(self, node: Any, environment: Dict[str, str], requested_extras: List[str]) -> bool:
        """Evaluate a parsed AST node."""
        if node is None:
            return True
        
        if node[0] == 'OR':
            return (self._evaluate_node(node[1], environment, requested_extras) or
                    self._evaluate_node(node[2], environment, requested_extras))
        elif node[0] == 'AND':
            return (self._evaluate_node(node[1], environment, requested_extras) and
                    self._evaluate_node(node[2], environment, requested_extras))
        elif node[0] == 'CMP':
            var_name = node[1]
            op = node[2]
            right_val = node[3]
            
            # Get the environment value
            if var_name == 'extra':
                if not requested_extras:
                    # Evaluate as empty string
                    left_val = ''
                else:
                    # True if any requested extra matches (after normalization)
                    return any(self._compare(extra, op, right_val) for extra in requested_extras)
            else:
                if var_name not in environment:
                    raise UndefinedEnvironmentName(f"Undefined environment variable: {var_name}")
                left_val = environment[var_name]
            
            return self._compare(left_val, op, right_val)
        
        raise InvalidMarker(f"Unknown node type: {node[0]}")
    
    def _compare(self, left: str, op: str, right: str) -> bool:
        """Compare two values with an operator."""
        # Try to parse as versions for version comparison
        try:
            left_version = Version(left)
            right_version = Version(right)
            # Both are valid versions, use version comparison
            if op == '==':
                return left_version == right_version
            elif op == '!=':
                return left_version != right_version
            elif op == '<':
                return left_version < right_version
            elif op == '<=':
                return left_version <= right_version
            elif op == '>':
                return left_version > right_version
            elif op == '>=':
                return left_version >= right_version
        except (InvalidVersion, ValueError):
            pass
        
        # String comparison
        if op == '==':
            return left == right
        elif op == '!=':
            return left != right
        elif op == '<':
            return left < right
        elif op == '<=':
            return left <= right
        elif op == '>':
            return left > right
        elif op == '>=':
            return left >= right
        elif op == 'in':
            return right in left
        elif op == 'not in':
            return right not in left
        
        raise InvalidMarker(f"Unknown operator: {op}")
    
    def __str__(self) -> str:
        """Return canonical marker string."""
        return self._node_to_string(self._parsed)
    
    def _node_to_string(self, node: Any) -> str:
        """Convert AST back to string."""
        if node is None:
            return ""
        
        if node[0] == 'OR':
            return f"{self._node_to_string(node[1])} or {self._node_to_string(node[2])}"
        elif node[0] == 'AND':
            return f"{self._node_to_string(node[1])} and {self._node_to_string(node[2])}"
        elif node[0] == 'CMP':
            return f"{node[1]} {node[2]} '{node[3]}'"
        
        return ""
    
    def __repr__(self) -> str:
        return f"Marker('{str(self)}')"
    
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Marker):
            return NotImplemented
        return str(self) == str(other)
    
    def __hash__(self) -> int:
        return hash(str(self))


# =============================================================================
# Environment
# =============================================================================

def default_environment() -> Dict[str, str]:
    """
    Return default environment dictionary for marker evaluation.
    
    Contains all supported variables except 'extra'.
    """
    env = {
        'os_name': os.name,
        'sys_platform': sys.platform,
        'platform_machine': platform.machine(),
        'platform_system': platform.system(),
        'platform_release': platform.release(),
        'platform_version': platform.version(),
        'platform_python_implementation': platform.python_implementation(),
    }
    
    # Python version
    env['python_version'] = f"{sys.version_info.major}.{sys.version_info.minor}"
    env['python_full_version'] = platform.python_version()
    
    # Implementation
    env['implementation_name'] = sys.implementation.name
    impl_version = sys.implementation.version
    env['implementation_version'] = f"{impl_version.major}.{impl_version.minor}.{impl_version.micro}"
    
    return env


# =============================================================================
# Requirement Satisfaction
# =============================================================================

def is_requirement_satisfied(
    requirement: Union[str, Requirement],
    installed_version: Union[str, Version],
    environment: Optional[Dict[str, str]] = None,
    requested_extras: Optional[List[str]] = None,
    prereleases: Optional[bool] = None
) -> bool:
    """
    Check if a requirement is satisfied by an installed version.
    
    Args:
        requirement: Requirement string or Requirement object
        installed_version: Version string or Version object
        environment: Environment dict for marker evaluation
        requested_extras: List of requested extras for 'extra' marker
        prereleases: Whether to consider pre-releases
    
    Returns:
        True if requirement is satisfied, False otherwise.
    
    Raises:
        InvalidRequirement: If requirement string is invalid
        InvalidVersion: If version string is invalid
        InvalidMarker: If marker is invalid
        UndefinedEnvironmentName: If marker needs undefined env variable
    """
    # Parse requirement if string
    if isinstance(requirement, str):
        requirement = Requirement(requirement)
    
    # Parse version if string
    if isinstance(installed_version, str):
        installed_version = Version(installed_version)
    
    # Check marker first
    if requirement.marker is not None:
        if not requirement.marker.evaluate(environment, requested_extras):
            # Marker doesn't apply, requirement is satisfied (doesn't apply)
            return True
    
    # Check version specifier
    if str(requirement.specifier):
        return requirement.specifier.contains(installed_version, prereleases)
    
    # No marker or specifier, requirement is satisfied
    return True