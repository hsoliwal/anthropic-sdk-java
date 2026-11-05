package com.anthropic.example;

import com.anthropic.client.AnthropicClient;
import com.anthropic.client.okhttp.AnthropicOkHttpClient;
import com.anthropic.core.JsonValue;
import com.anthropic.models.messages.JsonOutputFormat;
import com.anthropic.models.messages.MessageCreateParams;
import com.anthropic.models.messages.Model;
import com.anthropic.models.messages.OutputConfig;
import java.util.List;
import java.util.Map;

/**
 * An example of structured outputs using the low-level ("raw") API to define the JSON schema for
 * the output format. Compare to {@link StructuredOutputsExample} where the same JSON schema is
 * derived from the structure of Java classes.
 */
public final class StructuredOutputsRawExample {
    private static final String TYPE_KEY = "type";
    private static final String STRING_TYPE = "string";

    private StructuredOutputsRawExample() {}

    public static void main(String[] args) {
        // Configure by setting the `ANTHROPIC_API_KEY` environment variable.
        AnthropicClient client = AnthropicOkHttpClient.fromEnv();

        JsonOutputFormat.Schema schema = JsonOutputFormat.Schema.builder()
                // The "$schema" property can be omitted.
                .putAdditionalProperty(TYPE_KEY, JsonValue.from("object"))
                .putAdditionalProperty(
                        "properties",
                        JsonValue.from(Map.of(
                                "books",
                                Map.of(
                                        "minItems",
                                        1,
                                        TYPE_KEY,
                                        "array",
                                        "items",
                                        Map.of(
                                                TYPE_KEY,
                                                "object",
                                                "properties",
                                                Map.of(
                                                        "author",
                                                                Map.of(
                                                                        TYPE_KEY,
                                                                        "object",
                                                                        "properties",
                                                                        Map.of(
                                                                                "birthYear", Map.of(TYPE_KEY, "integer"),
                                                                                "deathYear",
                                                                                        Map.of(
                                                                                                TYPE_KEY,
                                                                                                STRING_TYPE,
                                                                                                "description",
                                                                                                "The year the person"
                                                                                                    + " died, or"
                                                                                                    + " 'present' if"
                                                                                                    + " the person is"
                                                                                                    + " living."),
                                                                                "name",
                                                                                        Map.of(
                                                                                                TYPE_KEY,
                                                                                                STRING_TYPE,
                                                                                                "description",
                                                                                                "The first"
                                                                                                        + " name"
                                                                                                        + " and surname"
                                                                                                        + " of the"
                                                                                                        + " person.")),
                                                                        "required",
                                                                        List.of("birthYear", "deathYear", "name"),
                                                                        "additionalProperties",
                                                                        false),
                                                        "genre", Map.of(TYPE_KEY, STRING_TYPE),
                                                        "publicationYear",
                                                                Map.of(
                                                                        TYPE_KEY,
                                                                        "integer",
                                                                        "description",
                                                                        "The year in which the book was first"
                                                                                + " published. No earlier than"
                                                                                + " 1500."),
                                                        "title", Map.of(TYPE_KEY, STRING_TYPE)),
                                                "required",
                                                List.of("author", "genre", "publicationYear", "title"),
                                                "additionalProperties",
                                                false)))))
                .putAdditionalProperty("required", JsonValue.from(List.of("books")))
                .putAdditionalProperty("additionalProperties", JsonValue.from(false))
                .build();

        OutputConfig outputConfig = OutputConfig.builder()
                .format(JsonOutputFormat.builder().schema(schema).build())
                .build();

        MessageCreateParams createParams = MessageCreateParams.builder()
                .model(Model.CLAUDE_SONNET_5_5)
                .maxTokens(2048)
                .outputConfig(outputConfig)
                .addUserMessage("List some famous late twentieth century novels.")
                .build();

        client.messages().create(createParams).content().stream()
                .flatMap(contentBlock -> contentBlock.text().stream())
                .forEach(textBlock -> System.out.println("JSON output: " + textBlock.text()));
    }
}
