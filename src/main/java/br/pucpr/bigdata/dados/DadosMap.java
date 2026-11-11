package br.pucpr.bigdata.dados;

import java.io.IOException;

import org.apache.hadoop.io.LongWritable;
import org.apache.hadoop.io.NullWritable;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Mapper;

// Le cada linha do CSV e devolve so as colunas numericas (month e day ficam de fora porque sao texto)
public class DadosMap extends Mapper<LongWritable, Text, NullWritable, Text> {

    // contadores que o Main usa para conferir se todas as linhas foram lidas
    public enum Linhas { VALIDAS, INVALIDAS }

    private static final int TOTAL_COLUNAS = 13;

    // X, Y, FFMC, DMC, DC, ISI, temp, RH, wind, rain, area
    private static final int[] INDICES_NUMERICOS = {0, 1, 4, 5, 6, 7, 8, 9, 10, 11, 12};

    private final Text linhaNumerica = new Text();

    @Override
    protected void map(LongWritable offset, Text linha, Context context)
            throws IOException, InterruptedException {

        String texto = linha.toString().trim();
        if (texto.isEmpty()) {
            return;
        }

        String[] colunas = texto.split(",");
        if (colunas.length != TOTAL_COLUNAS) {
            context.getCounter(Linhas.INVALIDAS).increment(1);
            return;
        }

        StringBuilder numeros = new StringBuilder();
        for (int indice : INDICES_NUMERICOS) {
            String valor = colunas[indice].trim();
            try {
                Double.parseDouble(valor);
            } catch (NumberFormatException e) {
                context.getCounter(Linhas.INVALIDAS).increment(1);
                return;
            }
            if (numeros.length() > 0) {
                numeros.append(',');
            }
            numeros.append(valor);
        }

        // escreve o valor original, sem arredondar, para o Python receber o dado igual ao do arquivo
        linhaNumerica.set(numeros.toString());
        context.write(NullWritable.get(), linhaNumerica);
        context.getCounter(Linhas.VALIDAS).increment(1);
    }
}
