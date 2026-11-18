/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   main.c                                             :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: asaadane <asaadane@student.42.fr>          +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2024/01/02 23:03:47 by asaadane          #+#    #+#             */
/*   Updated: 2026/11/18 19:43:00 by asaadane         ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "philo.h"

// Philosopher thread routine: staggered startup then eat-sleep-think cycle
static void	*thread_routine(void *philo)
{
	t_info	*p;

	p = (t_info *)philo;
	if (p->n_philo == 1)
	{
		manage_philos(p, FORK_TAKEN);
		ft_usleep(p->t_die);
		return (NULL);
	}
	if (p->id % 2 == 0)
	{
		philo_think(p);
		ft_usleep_until(p->start + (p->t_eat / 2));
	}
	while (1)
	{
		eat(p);
		philo_sleep(p);
		philo_think(p);
	}
	return (NULL);
}

// Free resources and destroy mutexes
void	clean_data(t_philo *info)
{
	int	i;

	if (!info)
		return ;
	if (info->forks)
	{
		i = -1;
		while (++i < info->n_philo)
			pthread_mutex_destroy(&info->forks[i]);
		free(info->forks);
	}
	pthread_mutex_destroy(&info->sync);
	if (info->philo)
		free(info->philo);
	free(info);
}

// Error manager
static int	error_manager(int code)
{
	if (code == 1)
		printf("Error : Malloc error\n");
	else if (code == 2)
		printf("Error : Couldn't create a thread\n");
	return (0);
}

// Main entry point
int	main(int argc, char **argv)
{
	int			i;
	t_philo		*info;
	pthread_t	*thread_id;

	info = (t_philo *)malloc(sizeof(t_philo));
	if (!info)
		return (error_manager(1));
	if (!parsing(argv, argc - 1, info))
		return (clean_data(info), 0);
	thread_id = (pthread_t *)malloc(info->n_philo * sizeof(pthread_t));
	if (!thread_id)
		return (clean_data(info), error_manager(1));
	i = -1;
	info->start = ft_time();
	while (++i < info->n_philo)
	{
		info->philo[i].start = info->start;
		info->philo[i].last_meal = info->start;
		info->err = pthread_create(&thread_id[i], NULL, thread_routine,
				&info->philo[i]);
		if (info->err)
			return (free(thread_id), clean_data(info), error_manager(2));
	}
	free(thread_id);
	return (check_philos(info));
}
