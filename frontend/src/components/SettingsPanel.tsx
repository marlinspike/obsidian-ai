import { useQuery } from "@tanstack/react-query";
import { X, Check, AlertCircle, Server } from "lucide-react";
import { getAvailableModels, getProviders, getCurrentModelConfig } from "@/services/api";

interface SettingsPanelProps {
  onClose: () => void;
}

export function SettingsPanel({ onClose }: SettingsPanelProps) {
  const { data: models } = useQuery({
    queryKey: ["availableModels"],
    queryFn: getAvailableModels,
  });

  const { data: providers } = useQuery({
    queryKey: ["providers"],
    queryFn: getProviders,
  });

  const { data: config } = useQuery({
    queryKey: ["modelConfig"],
    queryFn: getCurrentModelConfig,
  });

  const formatPrice = (price: string) => {
    const num = parseFloat(price);
    return num < 1 ? `$${num.toFixed(2)}` : `$${num.toFixed(2)}`;
  };

  const chatModels = models?.filter((m) => !m.is_embedding_model) || [];
  const embeddingModels = models?.filter((m) => m.is_embedding_model) || [];

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-2xl max-h-[80vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <Server className="h-5 w-5 text-obsidian-600" />
            Settings
          </h2>
          <button
            onClick={onClose}
            className="btn-ghost p-2 text-gray-500 hover:text-gray-700"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(80vh-60px)]">
          <div className="space-y-6">
            {/* Current Configuration */}
            {config && (
              <div>
                <h3 className="font-semibold text-gray-900 mb-3">
                  Current Configuration
                </h3>
                <div className="space-y-3">
                  <div className="p-3 rounded-lg bg-gray-50">
                    <div className="text-sm text-gray-600">Simple Queries</div>
                    <div className="font-medium">
                      {config.simple_query_model}{" "}
                      <span className="text-gray-500">
                        ({config.simple_query_provider})
                      </span>
                    </div>
                  </div>
                  <div className="p-3 rounded-lg bg-gray-50">
                    <div className="text-sm text-gray-600">Complex Queries</div>
                    <div className="font-medium">
                      {config.complex_query_model}{" "}
                      <span className="text-gray-500">
                        ({config.complex_query_provider})
                      </span>
                    </div>
                  </div>
                  <div className="p-3 rounded-lg bg-gray-50">
                    <div className="text-sm text-gray-600">Embeddings</div>
                    <div className="font-medium">
                      {config.embedding_model}{" "}
                      <span className="text-gray-500">
                        ({config.embedding_provider})
                      </span>
                    </div>
                  </div>
                </div>
                <p className="text-xs text-gray-500 mt-2">
                  To change models, update the .env file and restart the backend.
                </p>
              </div>
            )}

            {/* Provider Status */}
            {providers && (
              <div>
                <h3 className="font-semibold text-gray-900 mb-3">
                  Provider Status
                </h3>
                <div className="grid grid-cols-2 gap-3">
                  {providers.map((provider) => (
                    <div
                      key={provider.provider}
                      className={`p-3 rounded-lg border ${
                        provider.is_configured
                          ? "border-green-200 bg-green-50"
                          : "border-gray-200 bg-gray-50"
                      }`}
                    >
                      <div className="flex items-center gap-2 mb-1">
                        {provider.is_configured ? (
                          <Check className="h-4 w-4 text-green-600" />
                        ) : (
                          <AlertCircle className="h-4 w-4 text-gray-400" />
                        )}
                        <span className="font-medium">{provider.display_name}</span>
                      </div>
                      <div className="text-xs text-gray-500">
                        {provider.is_configured ? "Configured" : "Not configured"}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Available Models */}
            {chatModels.length > 0 && (
              <div>
                <h3 className="font-semibold text-gray-900 mb-3">
                  Chat Models
                </h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-left text-gray-500 border-b">
                        <th className="pb-2">Model</th>
                        <th className="pb-2">Provider</th>
                        <th className="pb-2 text-right">Input / 1M</th>
                        <th className="pb-2 text-right">Output / 1M</th>
                        <th className="pb-2 text-center">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {chatModels.map((model) => (
                        <tr
                          key={`${model.provider}-${model.model}`}
                          className="border-b border-gray-50"
                        >
                          <td className="py-2 font-medium">{model.display_name}</td>
                          <td className="py-2 capitalize">{model.provider}</td>
                          <td className="py-2 text-right font-mono">
                            {formatPrice(model.input_price_per_million)}
                          </td>
                          <td className="py-2 text-right font-mono">
                            {formatPrice(model.output_price_per_million)}
                          </td>
                          <td className="py-2 text-center">
                            {model.is_configured ? (
                              <Check className="h-4 w-4 text-green-600 mx-auto" />
                            ) : (
                              <AlertCircle className="h-4 w-4 text-gray-300 mx-auto" />
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Embedding Models */}
            {embeddingModels.length > 0 && (
              <div>
                <h3 className="font-semibold text-gray-900 mb-3">
                  Embedding Models
                </h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-left text-gray-500 border-b">
                        <th className="pb-2">Model</th>
                        <th className="pb-2">Provider</th>
                        <th className="pb-2 text-right">Price / 1M tokens</th>
                        <th className="pb-2 text-center">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {embeddingModels.map((model) => (
                        <tr
                          key={`${model.provider}-${model.model}`}
                          className="border-b border-gray-50"
                        >
                          <td className="py-2 font-medium">{model.display_name}</td>
                          <td className="py-2 capitalize">{model.provider}</td>
                          <td className="py-2 text-right font-mono">
                            {formatPrice(model.input_price_per_million)}
                          </td>
                          <td className="py-2 text-center">
                            {model.is_configured ? (
                              <Check className="h-4 w-4 text-green-600 mx-auto" />
                            ) : (
                              <AlertCircle className="h-4 w-4 text-gray-300 mx-auto" />
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
