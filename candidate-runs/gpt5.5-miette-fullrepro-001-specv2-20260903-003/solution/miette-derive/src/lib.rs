use proc_macro::TokenStream;

#[proc_macro_derive(
    Diagnostic,
    attributes(diagnostic, source_code, label, related, help, diagnostic_source)
)]
pub fn derive_diagnostic(input: TokenStream) -> TokenStream {
    match derive_impl(&input.to_string()) {
        Ok(output) => output.parse().unwrap_or_else(|err| {
            compile_error(&format!("failed to generate Diagnostic impl: {err}"))
        }),
        Err(err) => compile_error(&err),
    }
}

fn compile_error(message: &str) -> TokenStream {
    format!("compile_error!({:?});", message).parse().unwrap()
}

#[derive(Clone, Debug, Default)]
struct DiagnosticAttr {
    code: Option<Value>,
    severity: Option<String>,
    help: Option<Value>,
    url: Option<Value>,
    transparent: bool,
    forward: Option<String>,
}

#[derive(Clone, Debug)]
enum Value {
    Literal(String),
    Expr(String),
    CodePath(String),
    Docs,
}

#[derive(Clone, Debug, Default)]
struct FieldAttr {
    source_code: bool,
    label: bool,
    label_text: Option<String>,
    related: bool,
    help: bool,
    diagnostic_source: bool,
}

#[derive(Clone, Debug)]
struct Field {
    name: Option<String>,
    index: usize,
    attrs: FieldAttr,
}

#[derive(Clone, Debug)]
struct Variant {
    name: String,
    attrs: DiagnosticAttr,
    fields: Vec<Field>,
    style: VariantStyle,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum VariantStyle {
    Unit,
    Tuple,
    Struct,
}

#[derive(Clone, Debug)]
struct ItemInfo {
    name: String,
    generics_decl: String,
    type_generics: String,
    where_clause: String,
    attrs: DiagnosticAttr,
}

fn derive_impl(src: &str) -> Result<String, String> {
    let struct_pos = find_keyword(src, "struct");
    let enum_pos = find_keyword(src, "enum");
    match (struct_pos, enum_pos) {
        (Some(pos), None) => derive_struct(src, pos),
        (None, Some(pos)) => derive_enum(src, pos),
        (Some(s), Some(e)) if s < e => derive_struct(src, s),
        (Some(_), Some(e)) => derive_enum(src, e),
        _ => Err("Diagnostic can only be derived for structs and enums".into()),
    }
}

fn derive_struct(src: &str, pos: usize) -> Result<String, String> {
    let item = parse_item_info(src, pos, "struct")?;
    let (body, style) = item_body(src, pos).unwrap_or((String::new(), VariantStyle::Unit));
    let fields = match style {
        VariantStyle::Struct => parse_named_fields(&body),
        VariantStyle::Tuple => parse_tuple_fields(&body),
        VariantStyle::Unit => Vec::new(),
    };
    if item.attrs.transparent && fields.is_empty() {
        return Err("transparent diagnostics need a wrapped field".into());
    }
    Ok(impl_for_struct(item, fields))
}

fn derive_enum(src: &str, pos: usize) -> Result<String, String> {
    let item = parse_item_info(src, pos, "enum")?;
    let (body, _) = item_body(src, pos).ok_or("enum diagnostics need a body")?;
    let variants = parse_variants(&body);
    Ok(impl_for_enum(item, variants))
}

fn parse_item_info(src: &str, pos: usize, keyword: &str) -> Result<ItemInfo, String> {
    let attrs = parse_diagnostic_attrs(&src[..pos]);
    let mut rest = src[pos + keyword.len()..].trim_start();
    let name = take_ident(rest).ok_or_else(|| format!("expected {keyword} name"))?;
    rest = rest[name.len()..].trim_start();

    let mut generics_decl = String::new();
    if rest.starts_with('<') {
        let end = matching(rest, 0, '<', '>').ok_or("unclosed generic parameter list")?;
        generics_decl = rest[..=end].to_string();
        rest = rest[end + 1..].trim_start();
    }

    let body_start = rest
        .find(|ch| ch == '{' || ch == '(' || ch == ';')
        .unwrap_or(rest.len());
    let where_clause = rest[..body_start].trim().to_string();
    let type_generics = type_generics(&generics_decl);
    Ok(ItemInfo {
        name: name.to_string(),
        generics_decl,
        type_generics,
        where_clause,
        attrs,
    })
}

fn impl_for_struct(item: ItemInfo, fields: Vec<Field>) -> String {
    let target = struct_delegate_target(&item.attrs, &fields);
    let locals = struct_locals(&fields);
    let code_body = method_body_code(&item.attrs, target.as_deref(), &locals, "self");
    let severity_body = method_body_severity(&item.attrs, target.as_deref());
    let help_body = method_body_help(&item.attrs, &fields, target.as_deref(), &locals, "self");
    let url_body = method_body_url(&item.attrs, target.as_deref(), &locals, "self", &item.name);
    let source_body = method_body_source(&fields, target.as_deref(), false);
    let labels_body = method_body_labels(&fields, target.as_deref(), false);
    let related_body = method_body_related(&fields, target.as_deref(), false);
    let diag_source_body = method_body_diag_source(&fields, target.as_deref(), false);

    format!(
        "impl {impl_generics} ::miette::Diagnostic for {name}{type_generics} {where_clause} {{
            fn code<'a>(&'a self) -> Option<Box<dyn ::std::fmt::Display + 'a>> {{ {code_body} }}
            fn severity(&self) -> Option<::miette::Severity> {{ {severity_body} }}
            fn help<'a>(&'a self) -> Option<Box<dyn ::std::fmt::Display + 'a>> {{ {help_body} }}
            fn url<'a>(&'a self) -> Option<Box<dyn ::std::fmt::Display + 'a>> {{ {url_body} }}
            fn source_code(&self) -> Option<&dyn ::miette::SourceCode> {{ {source_body} }}
            fn labels(&self) -> Option<Box<dyn Iterator<Item = ::miette::LabeledSpan> + '_>> {{ {labels_body} }}
            fn related(&self) -> Option<Box<dyn Iterator<Item = &dyn ::miette::Diagnostic> + '_>> {{ {related_body} }}
            fn diagnostic_source(&self) -> Option<&dyn ::miette::Diagnostic> {{ {diag_source_body} }}
        }}",
        impl_generics = item.generics_decl,
        name = item.name,
        type_generics = item.type_generics,
        where_clause = item.where_clause,
    )
}

fn impl_for_enum(item: ItemInfo, variants: Vec<Variant>) -> String {
    let mut code_arms = String::new();
    let mut severity_arms = String::new();
    let mut help_arms = String::new();
    let mut url_arms = String::new();
    let mut source_arms = String::new();
    let mut labels_arms = String::new();
    let mut related_arms = String::new();
    let mut diag_source_arms = String::new();

    for variant in &variants {
        let pattern = variant_pattern(variant);
        let locals = enum_locals(variant);
        let target = enum_delegate_target(&variant.attrs, variant);
        let attrs = merge_attrs(&item.attrs, &variant.attrs);
        code_arms.push_str(&format!(
            "{pattern} => {{ {} }},",
            method_body_code(&attrs, target.as_deref(), &locals, "")
        ));
        severity_arms.push_str(&format!(
            "{pattern} => {{ {} }},",
            method_body_severity(&attrs, target.as_deref())
        ));
        help_arms.push_str(&format!(
            "{pattern} => {{ {} }},",
            method_body_help(&attrs, &variant.fields, target.as_deref(), &locals, "")
        ));
        url_arms.push_str(&format!(
            "{pattern} => {{ {} }},",
            method_body_url(&attrs, target.as_deref(), &locals, "", &variant.name)
        ));
        source_arms.push_str(&format!(
            "{pattern} => {{ {} }},",
            method_body_source(&variant.fields, target.as_deref(), true)
        ));
        labels_arms.push_str(&format!(
            "{pattern} => {{ {} }},",
            method_body_labels(&variant.fields, target.as_deref(), true)
        ));
        related_arms.push_str(&format!(
            "{pattern} => {{ {} }},",
            method_body_related(&variant.fields, target.as_deref(), true)
        ));
        diag_source_arms.push_str(&format!(
            "{pattern} => {{ {} }},",
            method_body_diag_source(&variant.fields, target.as_deref(), true)
        ));
    }

    format!(
        "impl {impl_generics} ::miette::Diagnostic for {name}{type_generics} {where_clause} {{
            fn code<'a>(&'a self) -> Option<Box<dyn ::std::fmt::Display + 'a>> {{ match self {{ {code_arms} }} }}
            fn severity(&self) -> Option<::miette::Severity> {{ match self {{ {severity_arms} }} }}
            fn help<'a>(&'a self) -> Option<Box<dyn ::std::fmt::Display + 'a>> {{ match self {{ {help_arms} }} }}
            fn url<'a>(&'a self) -> Option<Box<dyn ::std::fmt::Display + 'a>> {{ match self {{ {url_arms} }} }}
            fn source_code(&self) -> Option<&dyn ::miette::SourceCode> {{ match self {{ {source_arms} }} }}
            fn labels(&self) -> Option<Box<dyn Iterator<Item = ::miette::LabeledSpan> + '_>> {{ match self {{ {labels_arms} }} }}
            fn related(&self) -> Option<Box<dyn Iterator<Item = &dyn ::miette::Diagnostic> + '_>> {{ match self {{ {related_arms} }} }}
            fn diagnostic_source(&self) -> Option<&dyn ::miette::Diagnostic> {{ match self {{ {diag_source_arms} }} }}
        }}",
        impl_generics = item.generics_decl,
        name = item.name,
        type_generics = item.type_generics,
        where_clause = item.where_clause,
    )
}

fn merge_attrs(parent: &DiagnosticAttr, child: &DiagnosticAttr) -> DiagnosticAttr {
    DiagnosticAttr {
        code: child.code.clone().or_else(|| parent.code.clone()),
        severity: child.severity.clone().or_else(|| parent.severity.clone()),
        help: child.help.clone().or_else(|| parent.help.clone()),
        url: child.url.clone().or_else(|| parent.url.clone()),
        transparent: child.transparent || parent.transparent,
        forward: child.forward.clone().or_else(|| parent.forward.clone()),
    }
}

fn method_body_code(
    attrs: &DiagnosticAttr,
    target: Option<&str>,
    locals: &str,
    _self_prefix: &str,
) -> String {
    if let Some(value) = &attrs.code {
        return format!("{locals} {}", display_value(value, "code"));
    }
    if let Some(target) = target {
        return format!("let __miette_target: &dyn ::miette::Diagnostic = {target}; __miette_target.code()");
    }
    "None".into()
}

fn method_body_severity(attrs: &DiagnosticAttr, target: Option<&str>) -> String {
    if let Some(severity) = &attrs.severity {
        return format!("Some(::miette::Severity::{})", normalize_variant(severity));
    }
    if let Some(target) = target {
        return format!("let __miette_target: &dyn ::miette::Diagnostic = {target}; __miette_target.severity()");
    }
    "None".into()
}

fn method_body_help(
    attrs: &DiagnosticAttr,
    fields: &[Field],
    target: Option<&str>,
    locals: &str,
    _self_prefix: &str,
) -> String {
    if let Some(value) = &attrs.help {
        return format!("{locals} {}", display_value(value, "help"));
    }
    if let Some(field) = fields.iter().find(|field| field.attrs.help) {
        return format!(
            "::miette::__private::AsDisplay::as_display({})",
            field_ref(field, false)
        );
    }
    if let Some(target) = target {
        return format!("let __miette_target: &dyn ::miette::Diagnostic = {target}; __miette_target.help()");
    }
    "None".into()
}

fn method_body_url(
    attrs: &DiagnosticAttr,
    target: Option<&str>,
    locals: &str,
    _self_prefix: &str,
    item_name: &str,
) -> String {
    if let Some(value) = &attrs.url {
        return match value {
            Value::Docs => format!(
                "Some(Box::new(format!(\"https://docs.rs/{{}}/latest/{{}}/{{}}\", env!(\"CARGO_PKG_NAME\"), module_path!(), {:?})))",
                item_name
            ),
            _ => format!("{locals} {}", display_value(value, "url")),
        };
    }
    if let Some(target) = target {
        return format!("let __miette_target: &dyn ::miette::Diagnostic = {target}; __miette_target.url()");
    }
    "None".into()
}

fn method_body_source(fields: &[Field], target: Option<&str>, enum_mode: bool) -> String {
    if let Some(field) = fields.iter().find(|field| field.attrs.source_code) {
        return format!(
            "::miette::__private::AsSourceCode::as_source_code({})",
            field_ref(field, enum_mode)
        );
    }
    if let Some(target) = target {
        return format!("let __miette_target: &dyn ::miette::Diagnostic = {target}; __miette_target.source_code()");
    }
    "None".into()
}

fn method_body_labels(fields: &[Field], target: Option<&str>, enum_mode: bool) -> String {
    let label_fields: Vec<_> = fields.iter().filter(|field| field.attrs.label).collect();
    if !label_fields.is_empty() {
        let mut body = String::from("let mut __miette_labels = Vec::new();");
        for field in label_fields {
            let text = field
                .attrs
                .label_text
                .as_ref()
                .map(|value| format!("Some({value:?})"))
                .unwrap_or_else(|| "None".into());
            body.push_str(&format!(
                "if let Some(mut __miette_more) = ::miette::__private::AsLabels::as_labels({}, {text}) {{ __miette_labels.append(&mut __miette_more); }}",
                field_ref(field, enum_mode)
            ));
        }
        body.push_str("if __miette_labels.is_empty() { None } else { Some(Box::new(__miette_labels.into_iter())) }");
        return body;
    }
    if let Some(target) = target {
        return format!("let __miette_target: &dyn ::miette::Diagnostic = {target}; __miette_target.labels()");
    }
    "None".into()
}

fn method_body_related(fields: &[Field], target: Option<&str>, enum_mode: bool) -> String {
    if let Some(field) = fields.iter().find(|field| field.attrs.related) {
        return format!(
            "let __miette_related = ::miette::__private::AsRelated::as_related({}); if __miette_related.is_empty() {{ None }} else {{ Some(Box::new(__miette_related.into_iter())) }}",
            field_ref(field, enum_mode)
        );
    }
    if let Some(target) = target {
        return format!("let __miette_target: &dyn ::miette::Diagnostic = {target}; __miette_target.related()");
    }
    "None".into()
}

fn method_body_diag_source(fields: &[Field], target: Option<&str>, enum_mode: bool) -> String {
    if let Some(field) = fields.iter().find(|field| field.attrs.diagnostic_source) {
        return format!(
            "::miette::__private::AsDiagnosticSource::as_diagnostic_source({})",
            field_ref(field, enum_mode)
        );
    }
    if let Some(target) = target {
        return format!("let __miette_target: &dyn ::miette::Diagnostic = {target}; __miette_target.diagnostic_source()");
    }
    "None".into()
}

fn display_value(value: &Value, kind: &str) -> String {
    match value {
        Value::Literal(lit) => format!("Some(Box::new(format!({lit})))"),
        Value::Expr(expr) => format!("Some(Box::new(format!(\"{{}}\", {expr})))"),
        Value::CodePath(path) if kind == "code" => {
            format!("Some(Box::new(::miette::__private::normalize_code(stringify!({path}))))")
        }
        Value::CodePath(path) => format!("Some(Box::new(format!(\"{{}}\", {path})))"),
        Value::Docs => "None".into(),
    }
}

fn struct_delegate_target(attrs: &DiagnosticAttr, fields: &[Field]) -> Option<String> {
    if attrs.transparent {
        return fields.first().map(|field| field_ref(field, false));
    }
    attrs
        .forward
        .as_ref()
        .and_then(|name| find_field(fields, name))
        .map(|field| field_ref(field, false))
}

fn enum_delegate_target(attrs: &DiagnosticAttr, variant: &Variant) -> Option<String> {
    if attrs.transparent {
        return variant.fields.first().map(|field| field_ref(field, true));
    }
    attrs
        .forward
        .as_ref()
        .and_then(|name| find_field(&variant.fields, name))
        .map(|field| field_ref(field, true))
}

fn find_field<'a>(fields: &'a [Field], name: &str) -> Option<&'a Field> {
    let needle = name.trim();
    fields.iter().find(|field| {
        field
            .name
            .as_deref()
            .map(|field_name| field_name == needle)
            .unwrap_or_else(|| field.index.to_string() == needle)
    })
}

fn field_ref(field: &Field, enum_mode: bool) -> String {
    if enum_mode {
        field
            .name
            .clone()
            .unwrap_or_else(|| format!("__miette_field_{}", field.index))
    } else if let Some(name) = &field.name {
        format!("&self.{name}")
    } else {
        format!("&self.{}", field.index)
    }
}

fn struct_locals(fields: &[Field]) -> String {
    let mut out = String::new();
    for field in fields {
        if let Some(name) = &field.name {
            out.push_str(&format!("let {name} = &self.{name};"));
        }
    }
    out
}

fn enum_locals(variant: &Variant) -> String {
    match variant.style {
        VariantStyle::Struct | VariantStyle::Tuple => String::new(),
        VariantStyle::Unit => String::new(),
    }
}

fn variant_pattern(variant: &Variant) -> String {
    match variant.style {
        VariantStyle::Unit => format!("Self::{}", variant.name),
        VariantStyle::Tuple => {
            let fields = (0..variant.fields.len())
                .map(|idx| format!("__miette_field_{idx}"))
                .collect::<Vec<_>>()
                .join(", ");
            format!("Self::{}({fields})", variant.name)
        }
        VariantStyle::Struct => {
            let fields = variant
                .fields
                .iter()
                .filter_map(|field| field.name.clone())
                .collect::<Vec<_>>()
                .join(", ");
            format!("Self::{} {{ {fields} }}", variant.name)
        }
    }
}

fn parse_diagnostic_attrs(src: &str) -> DiagnosticAttr {
    let mut out = DiagnosticAttr::default();
    for body in attr_bodies(src, "diagnostic") {
        for option in split_top_level(&body, ',') {
            let option = option.trim();
            if option.is_empty() {
                continue;
            }
            if option == "transparent" {
                out.transparent = true;
            } else if let Some(inner) = call_inner(option, "forward") {
                out.forward = Some(clean_path(inner));
            } else if let Some(value) = option_value(option, "code") {
                out.code = Some(if is_literal(value) {
                    Value::Literal(value.to_string())
                } else {
                    Value::CodePath(value.to_string())
                });
            } else if let Some(value) = option_value(option, "severity") {
                out.severity = Some(value.to_string());
            } else if let Some(value) = option_value(option, "help") {
                out.help = Some(parse_value(value));
            } else if let Some(value) = option_value(option, "url") {
                if clean_path(value) == "docsrs" {
                    out.url = Some(Value::Docs);
                } else {
                    out.url = Some(parse_value(value));
                }
            }
        }
    }
    out
}

fn parse_field_attrs(src: &str) -> FieldAttr {
    let mut out = FieldAttr::default();
    if has_attr(src, "source_code") {
        out.source_code = true;
    }
    if has_attr(src, "related") {
        out.related = true;
    }
    if has_attr(src, "help") {
        out.help = true;
    }
    if has_attr(src, "diagnostic_source") {
        out.diagnostic_source = true;
    }
    if has_attr(src, "label") {
        out.label = true;
        if let Some(body) = attr_bodies(src, "label").into_iter().next() {
            let body = body.trim();
            if is_literal(body) {
                out.label_text = Some(unquote(body));
            }
        }
    }
    out
}

fn parse_named_fields(body: &str) -> Vec<Field> {
    split_top_level(body, ',')
        .into_iter()
        .enumerate()
        .filter_map(|(index, raw)| {
            let raw = raw.trim();
            if raw.is_empty() {
                return None;
            }
            let attrs = parse_field_attrs(raw);
            let clean = remove_attrs(raw);
            let before_colon = clean.split(':').next()?.trim();
            let name = before_colon
                .split_whitespace()
                .last()
                .filter(|part| !part.is_empty())?
                .to_string();
            Some(Field {
                name: Some(name),
                index,
                attrs,
            })
        })
        .collect()
}

fn parse_tuple_fields(body: &str) -> Vec<Field> {
    split_top_level(body, ',')
        .into_iter()
        .enumerate()
        .filter_map(|(index, raw)| {
            let raw = raw.trim();
            if raw.is_empty() {
                return None;
            }
            Some(Field {
                name: None,
                index,
                attrs: parse_field_attrs(raw),
            })
        })
        .collect()
}

fn parse_variants(body: &str) -> Vec<Variant> {
    split_top_level(body, ',')
        .into_iter()
        .filter_map(|raw| {
            let raw = raw.trim();
            if raw.is_empty() {
                return None;
            }
            let attrs = parse_diagnostic_attrs(raw);
            let clean = remove_leading_attrs(raw);
            let name = take_ident(clean.trim())?.to_string();
            let rest = clean.trim()[name.len()..].trim_start();
            if rest.starts_with('{') {
                let end = matching(rest, 0, '{', '}')?;
                let fields = parse_named_fields(&rest[1..end]);
                Some(Variant {
                    name,
                    attrs,
                    fields,
                    style: VariantStyle::Struct,
                })
            } else if rest.starts_with('(') {
                let end = matching(rest, 0, '(', ')')?;
                let fields = parse_tuple_fields(&rest[1..end]);
                Some(Variant {
                    name,
                    attrs,
                    fields,
                    style: VariantStyle::Tuple,
                })
            } else {
                Some(Variant {
                    name,
                    attrs,
                    fields: Vec::new(),
                    style: VariantStyle::Unit,
                })
            }
        })
        .collect()
}

fn item_body(src: &str, pos: usize) -> Option<(String, VariantStyle)> {
    let rest = &src[pos..];
    let brace = rest.find('{').map(|idx| (idx, '{', '}'));
    let paren = rest.find('(').map(|idx| (idx, '(', ')'));
    let semi = rest.find(';');
    let first_group = match (brace, paren) {
        (Some(a), Some(b)) => {
            if a.0 < b.0 {
                Some(a)
            } else {
                Some(b)
            }
        }
        (Some(a), None) => Some(a),
        (None, Some(b)) => Some(b),
        (None, None) => None,
    }?;
    if let Some(semi) = semi {
        if semi < first_group.0 {
            return Some((String::new(), VariantStyle::Unit));
        }
    }
    let start = pos + first_group.0;
    let end = matching(src, start, first_group.1, first_group.2)?;
    let style = if first_group.1 == '{' {
        VariantStyle::Struct
    } else {
        VariantStyle::Tuple
    };
    Some((src[start + 1..end].to_string(), style))
}

fn find_keyword(src: &str, keyword: &str) -> Option<usize> {
    let bytes = src.as_bytes();
    let needle = keyword.as_bytes();
    let mut i = 0usize;
    while i + needle.len() <= bytes.len() {
        if &bytes[i..i + needle.len()] == needle {
            let before = i == 0 || !is_ident_byte(bytes[i - 1]);
            let after = i + needle.len() == bytes.len() || !is_ident_byte(bytes[i + needle.len()]);
            if before && after {
                return Some(i);
            }
        }
        i += 1;
    }
    None
}

fn take_ident(src: &str) -> Option<&str> {
    let src = src.trim_start();
    let mut end = 0usize;
    for (idx, ch) in src.char_indices() {
        if idx == 0 {
            if !(ch == '_' || ch.is_ascii_alphabetic()) {
                return None;
            }
            end = ch.len_utf8();
        } else if ch == '_' || ch.is_ascii_alphanumeric() {
            end = idx + ch.len_utf8();
        } else {
            break;
        }
    }
    if end == 0 {
        None
    } else {
        Some(&src[..end])
    }
}

fn is_ident_byte(byte: u8) -> bool {
    byte == b'_' || byte.is_ascii_alphanumeric()
}

fn matching(src: &str, start: usize, open: char, close: char) -> Option<usize> {
    let mut depth = 0usize;
    let mut in_string = false;
    let mut escape = false;
    for (idx, ch) in src[start..].char_indices() {
        let absolute = start + idx;
        if in_string {
            if escape {
                escape = false;
            } else if ch == '\\' {
                escape = true;
            } else if ch == '"' {
                in_string = false;
            }
            continue;
        }
        if ch == '"' {
            in_string = true;
        } else if ch == open {
            depth += 1;
        } else if ch == close {
            depth -= 1;
            if depth == 0 {
                return Some(absolute);
            }
        }
    }
    None
}

fn split_top_level(src: &str, sep: char) -> Vec<String> {
    let mut out = Vec::new();
    let mut start = 0usize;
    let mut paren = 0usize;
    let mut brace = 0usize;
    let mut bracket = 0usize;
    let mut angle = 0usize;
    let mut in_string = false;
    let mut escape = false;
    for (idx, ch) in src.char_indices() {
        if in_string {
            if escape {
                escape = false;
            } else if ch == '\\' {
                escape = true;
            } else if ch == '"' {
                in_string = false;
            }
            continue;
        }
        match ch {
            '"' => in_string = true,
            '(' => paren += 1,
            ')' => paren = paren.saturating_sub(1),
            '{' => brace += 1,
            '}' => brace = brace.saturating_sub(1),
            '[' => bracket += 1,
            ']' => bracket = bracket.saturating_sub(1),
            '<' => angle += 1,
            '>' => angle = angle.saturating_sub(1),
            c if c == sep && paren == 0 && brace == 0 && bracket == 0 && angle == 0 => {
                out.push(src[start..idx].to_string());
                start = idx + ch.len_utf8();
            }
            _ => {}
        }
    }
    out.push(src[start..].to_string());
    out
}

fn attr_bodies(src: &str, name: &str) -> Vec<String> {
    let mut out = Vec::new();
    let mut offset = 0usize;
    while let Some(pos) = src[offset..].find(name) {
        let pos = offset + pos;
        let after = pos + name.len();
        if after < src.len() && is_ident_byte(src.as_bytes()[after]) {
            offset = after;
            continue;
        }
        let rest = src[after..].trim_start();
        if rest.starts_with('(') {
            let paren_start = after + src[after..].find('(').unwrap();
            if let Some(end) = matching(src, paren_start, '(', ')') {
                out.push(src[paren_start + 1..end].to_string());
                offset = end + 1;
                continue;
            }
        } else {
            out.push(String::new());
        }
        offset = after;
    }
    out
}

fn has_attr(src: &str, name: &str) -> bool {
    let needle = format!("[{name}");
    src.contains(&needle) || src.contains(&format!("[ {name}"))
}

fn remove_attrs(src: &str) -> String {
    let mut out = String::new();
    let mut i = 0usize;
    let bytes = src.as_bytes();
    while i < src.len() {
        if bytes[i] == b'#' {
            let rest = &src[i..];
            if let Some(open_rel) = rest.find('[') {
                let open = i + open_rel;
                if let Some(close) = matching(src, open, '[', ']') {
                    i = close + 1;
                    continue;
                }
            }
        }
        let ch = src[i..].chars().next().unwrap();
        out.push(ch);
        i += ch.len_utf8();
    }
    out
}

fn remove_leading_attrs(src: &str) -> String {
    let mut i = 0usize;
    loop {
        let rest = src[i..].trim_start();
        i = src.len() - rest.len();
        if !rest.starts_with('#') {
            break;
        }
        if let Some(open_rel) = rest.find('[') {
            let open = i + open_rel;
            if let Some(close) = matching(src, open, '[', ']') {
                i = close + 1;
                continue;
            }
        }
        break;
    }
    src[i..].to_string()
}

fn call_inner<'a>(src: &'a str, name: &str) -> Option<&'a str> {
    let src = src.trim();
    if !src.starts_with(name) {
        return None;
    }
    let rest = src[name.len()..].trim_start();
    if !rest.starts_with('(') {
        return None;
    }
    let end = matching(rest, 0, '(', ')')?;
    Some(rest[1..end].trim())
}

fn option_value<'a>(src: &'a str, name: &str) -> Option<&'a str> {
    if let Some(inner) = call_inner(src, name) {
        return Some(inner);
    }
    let src = src.trim();
    if !src.starts_with(name) {
        return None;
    }
    let rest = src[name.len()..].trim_start();
    rest.strip_prefix('=').map(str::trim)
}

fn parse_value(src: &str) -> Value {
    let src = src.trim();
    if is_literal(src) {
        Value::Literal(src.to_string())
    } else {
        Value::Expr(clean_path(src))
    }
}

fn is_literal(src: &str) -> bool {
    src.trim_start().starts_with('"')
}

fn unquote(src: &str) -> String {
    let src = src.trim();
    if src.len() >= 2 && src.starts_with('"') && src.ends_with('"') {
        src[1..src.len() - 1].replace("\\\"", "\"").replace("\\n", "\n")
    } else {
        src.to_string()
    }
}

fn clean_path(src: &str) -> String {
    src.split_whitespace().collect::<String>()
}

fn normalize_variant(src: &str) -> String {
    let src = clean_path(src);
    src.rsplit("::").next().unwrap_or(&src).to_string()
}

fn type_generics(generics: &str) -> String {
    if generics.trim().is_empty() {
        return String::new();
    }
    let inner = generics.trim().trim_start_matches('<').trim_end_matches('>');
    let params = split_top_level(inner, ',')
        .into_iter()
        .filter_map(|param| {
            let param = param.trim();
            if param.is_empty() {
                return None;
            }
            if param.starts_with("const ") {
                return param.split_whitespace().nth(1).map(str::to_string);
            }
            if param.starts_with('\'') {
                let name = param
                    .split(|ch: char| ch == ':' || ch == '=' || ch == ',' || ch.is_whitespace())
                    .next()
                    .unwrap_or(param);
                return Some(name.to_string());
            }
            let name = param
                .split(|ch: char| ch == ':' || ch == '=' || ch.is_whitespace())
                .next()
                .unwrap_or(param);
            Some(name.to_string())
        })
        .collect::<Vec<_>>();
    if params.is_empty() {
        String::new()
    } else {
        format!("<{}>", params.join(", "))
    }
}
