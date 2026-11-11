package br.pucpr.bigdata.dados;

import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.fs.Path;
import org.apache.hadoop.io.NullWritable;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Counters;
import org.apache.hadoop.mapreduce.Job;
import org.apache.hadoop.mapreduce.lib.input.FileInputFormat;
import org.apache.hadoop.mapreduce.lib.output.FileOutputFormat;

// Classe principal: roda o job que busca no Hadoop as 11 colunas numericas de cada linha do dataset
public class DadosMain {

    public static void main(String[] args) throws Exception {
        if (args.length != 2) {
            System.err.println("Uso: DadosMain <entrada> <saida>");
            System.exit(1);
        }

        Job job = Job.getInstance(new Configuration(), "dados-numericos");
        job.setJarByClass(DadosMain.class);
        job.setMapperClass(DadosMap.class);

        // sem Reduce: cada linha ja sai pronta do Map, na mesma ordem do arquivo
        job.setNumReduceTasks(0);

        job.setOutputKeyClass(NullWritable.class);
        job.setOutputValueClass(Text.class);

        FileInputFormat.addInputPath(job, new Path(args[0]));
        FileOutputFormat.setOutputPath(job, new Path(args[1]));

        if (!job.waitForCompletion(true)) {
            System.exit(1);
        }

        // confere a integridade: o job falha se alguma linha ficou de fora
        Counters contadores = job.getCounters();
        long validas = contadores.findCounter(DadosMap.Linhas.VALIDAS).getValue();
        long invalidas = contadores.findCounter(DadosMap.Linhas.INVALIDAS).getValue();
        System.out.println("Linhas validas: " + validas + " | invalidas: " + invalidas);
        System.exit(invalidas == 0 ? 0 : 1);
    }
}
